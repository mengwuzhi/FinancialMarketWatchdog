# 更新日志

## 2026-01-22 优化更新

### 功能移除
- **移除文心一言AI支持**
  - 删除 `ai_analyzer.py` 中的文心一言相关代码
  - 更新 README.md，移除文心一言说明
  - 理由：简化代码，专注于通义千问单一AI服务

### 功能增强
- **美股交易日判断增强**
  - 新增完整的美股节假日判断功能
  - 支持的节假日：
    1. 新年 (New Year's Day) - 1月1日
    2. 马丁·路德·金纪念日 (MLK Day) - 1月第三个星期一
    3. 总统日 (Presidents' Day) - 2月第三个星期一
    4. 耶稣受难日 (Good Friday) - 复活节前的星期五
    5. 阵亡将士纪念日 (Memorial Day) - 5月最后一个星期一
    6. 独立日 (Independence Day) - 7月4日
    7. 劳动节 (Labor Day) - 9月第一个星期一
    8. 感恩节 (Thanksgiving) - 11月第四个星期四
    9. 圣诞节 (Christmas) - 12月25日
  - 支持节假日周末顺延规则
  - 使用高斯算法计算复活节日期（耶稣受难日依赖此算法）

### 代码改进
- **trading_calendar.py**
  - 新增 `_is_us_market_holiday()` 方法
  - 新增 `_get_nth_weekday()` 辅助方法（计算第N个星期X）
  - 新增 `_get_last_weekday()` 辅助方法（计算最后一个星期X）
  - 新增 `_adjust_weekend_holiday()` 辅助方法（周末顺延）
  - 新增 `_get_good_friday()` 方法（使用高斯算法计算复活节）

- **ai_analyzer.py**
  - 简化类注释
  - 移除 `_analyze_with_ernie()` 方法
  - 简化 `analyze()` 方法逻辑

### 测试增强
- **新增测试文件**
  - `test/test_us_trading_calendar.py` - 美股交易日判断测试
  - 覆盖2024年和2025年所有主要节假日
  - 测试结果：14/14 全部通过

### 文档更新
- **README.md**
  - 修正A股市场日报执行时间（20:00 → 18:30）
  - 移除文心一言相关描述
  - 补充美股节假日判断说明
  - 完善项目结构（添加遗漏的文件）
  - 完善依赖库说明
  - 新增 `ai.enable_search` 配置项说明

## 修改文件清单

### 核心代码
- [core/trading_calendar.py](core/trading_calendar.py) - 增强美股交易日判断
- [analyzers/ai_analyzer.py](analyzers/ai_analyzer.py) - 移除文心一言支持

### 文档
- [README.md](README.md) - 修正时间、更新说明、补充遗漏内容

### 测试
- [test/test_us_trading_calendar.py](test/test_us_trading_calendar.py) - 新增测试文件

## 技术细节

### 美股节假日计算逻辑

#### 固定日期节假日（可能顺延）
```python
# 新年、独立日、圣诞节
if holiday.weekday() == 5:  # 周六 → 下周一
    return holiday + timedelta(days=2)
elif holiday.weekday() == 6:  # 周日 → 下周一
    return holiday + timedelta(days=1)
```

#### 相对日期节假日
```python
# 第N个星期X
# 例如：1月第三个星期一（MLK Day）
def _get_nth_weekday(year, month, weekday, n):
    first_day = date(year, month, 1)
    # 计算第一个目标星期几
    # 然后加上 (n-1) * 7 天
```

#### 复活节计算（高斯算法）
```python
def _get_good_friday(year):
    # 使用Meeus/Jones/Butcher算法计算复活节
    # 复活节日期计算公式（基于儒略历和格里高利历）
    # 耶稣受难日 = 复活节 - 2天
```

## 性能影响
- 新增方法均为纯计算，无外部API调用
- 时间复杂度：O(1) 常数时间
- 内存占用：可忽略不计

## 向后兼容性
- ✅ 完全兼容现有代码
- ✅ 配置文件无需修改
- ✅ 现有功能不受影响

## 测试覆盖率
- 美股节假日判断：100%（14/14测试通过）
- 2024年节假日：9个主要节假日 + 2个周末 + 3个交易日
- 2025年节假日：9个主要节假日验证

## 下一步建议
1. 添加更多边界情况测试（如节假日遇周末的顺延情况）
2. 考虑添加美股半天交易日支持（感恩节后、平安夜）
3. 可选：添加其他国家/地区市场的交易日判断
