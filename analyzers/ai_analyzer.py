import json
from typing import Dict, Optional

import requests


class AIAnalyzer:
    """AI分析器（使用通义千问）"""

    def __init__(
        self,
        provider: str,
        api_key: str,
        api_base_url: str,
        model: str,
        enable_search: bool = False,
    ):
        self.provider = provider
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model = model
        self.enable_search = enable_search

    def analyze(self, article_content: str) -> Dict:
        """
        分析文章内容

        Args:
            article_content: 文章内容

        Returns:
            分析结果字典
        """
        if self.provider == "qwen":
            return self._analyze_with_qwen(article_content)
        else:
            print(f"[ERROR] Unsupported AI provider: {self.provider}, only 'qwen' is supported")
            return self._get_empty_result()

    def _analyze_with_qwen(self, content: str) -> Dict:
        """使用通义千问分析"""
        try:
            prompt = self._build_prompt(content)
            url = f"{self.api_base_url}/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 3000,  # 增加token限制以支持更复杂的输出
            }

            # 如果启用搜索功能，添加到payload
            if self.enable_search:
                payload["enable_search"] = True

            # 根据是否启用搜索调整超时时间
            timeout = 120 if self.enable_search else 30
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()

            result = response.json()
            content_text = result["choices"][0]["message"]["content"]

            # 解析JSON响应
            return self._parse_response(content_text)

        except Exception as e:
            print(f"[ERROR] Qwen API call failed: {e}")
            return self._get_empty_result()

    def _build_prompt(self, content: str) -> str:
        """构建分析提示词"""
        return f"""你是一名投资市场研究分析助手。请按以下**两步流程**分析文章：

## 第一步：提取文章原始信息（不做延伸）
严格基于文章内容，提取所有投资市场相关信息，**不使用搜索**，**不做任何延伸推测**。

需覆盖的投资品种类型：
- **上市公司股票**：A股（沪深北交易所）、港股、美股
- **行业板块**：半导体、新能源、金融、消费等
- **投资主题**：贵金属（黄金、白银）、数字货币（比特币、以太坊）、大宗商品（原油、铜等）
- **基金产品**：ETF、公募基金、私募基金（注：此处仅用于文章信息提取识别，不代表系统具有这些基金的监控功能）

提取要求：
- 只提取文章明确提到的内容
- **stocks字段仅包含已上市公司**，必须标注市场和代码：
  - A股：6位数字代码（如600519、000001、300750）
  - 港股：5位数字代码（如00700、09988）
  - 美股：股票代码（如AAPL、TSLA、BABA）
  - **如不确定公司是否上市或代码不明确，使用搜索功能核实后再填入**
  - 非上市公司、拟上市公司一律不得出现在stocks字段中
- 非上市公司对行业的影响体现在industries字段的reason中

## 第二步：结合搜索的延伸分析
针对第一步识别出的**具体投资品种**（股票、基金、贵金属、数字货币等），使用网络搜索获取最新信息，总结投资观点和市场趋势。

要求：
- 仅针对文章提到的投资品种进行延伸
- 使用搜索获取最新价格、走势、市场情绪等
- 总结当前市场对这些品种的主流观点
- 分析潜在的投资机会和风险

请以JSON格式返回分析结果：

{{
    "core_summary": "文章核心观点总结（仅基于文章内容）",
    "market_view": "文章对市场的观点（看多/看空/中性/未明确）",
    "related_items": {{
        "stocks": [
            {{
                "code": "股票代码（A股6位数字如600519，港股5位如00700，美股如AAPL）",
                "name": "上市公司名称",
                "market": "市场标识（A股/港股/美股）",
                "reason": "文章中被提及的背景和原因"
            }}
        ],
        "industries": [
            {{
                "name": "行业板块名称",
                "reason": "文章中被提及的原因（如涉及非上市公司，说明其影响）"
            }}
        ],
        "investment_themes": [
            {{
                "name": "投资品种或主题（黄金、白银、比特币、原油等）",
                "reason": "文章中提及的背景"
            }}
        ],
        "funds": [
            {{
                "code": "基金/ETF代码",
                "name": "基金名称",
                "type": "类型（ETF/公募基金/私募基金）",
                "reason": "文章中被提及的背景"
            }}
        ]
    }},
    "potential_impact": {{
        "positive": ["文章提到的正面影响1", "正面影响2"],
        "negative": ["文章提到的负面影响1", "负面影响2"],
        "neutral": ["文章提到的中性观察1", "中性观察2"]
    }},
    "investment_insights": [
        "基于文章的投资启示1",
        "基于文章的投资启示2"
    ],
    "extended_analysis": {{
        "market_trends": [
            {{
                "item": "投资品种名称（如：贵州茅台、比特币、黄金等）",
                "current_view": "结合搜索得到的市场主流观点",
                "latest_info": "最新价格/走势/重要消息",
                "opportunity": "潜在投资机会",
                "risk": "需关注的风险"
            }}
        ],
        "summary": "结合搜索后的综合分析总结"
    }}
}}

文章内容：
{content}
"""

    def _parse_response(self, response_text: str) -> Dict:
        """解析AI响应"""
        try:
            # 尝试直接解析JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果不是标准JSON，尝试提取JSON部分
            try:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_text = response_text[start:end]
                    return json.loads(json_text)
            except Exception as e:
                print(f"[WARN] Failed to parse JSON: {e}")

            # 如果都失败，返回空结果
            return self._get_empty_result()

    def _get_empty_result(self) -> Dict:
        """返回空结果"""
        return {
            "core_summary": "分析失败",
            "market_view": "未知",
            "related_items": {
                "stocks": [],
                "industries": [],
                "investment_themes": [],
                "funds": []
            },
            "potential_impact": {
                "positive": [],
                "negative": [],
                "neutral": []
            },
            "investment_insights": [],
            "extended_analysis": {
                "market_trends": [],
                "summary": ""
            }
        }
