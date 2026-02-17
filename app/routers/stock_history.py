"""Stock history data API endpoints."""

import logging
from datetime import date, datetime
from threading import Thread
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market/stock", tags=["stock-history"])


class StockHistoryRequest(BaseModel):
    """Stock history query/download request."""

    market: Literal["cn", "us"] = Field(
        ...,
        description="Market type: 'cn' for A-share, 'us' for US stock"
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock symbol (e.g., '600000' for CN, 'AAPL' for US)"
    )

    start_date: str = Field(
        ...,
        description="Start date in YYYY-MM-DD format"
    )

    end_date: str = Field(
        ...,
        description="End date in YYYY-MM-DD format"
    )

    action: Literal["query", "save"] = Field(
        default="query",
        description="'query' to return data, 'save' to save to database"
    )

    adjust: Optional[Literal["qfq", "hfq", ""]] = Field(
        default="qfq",
        description="Adjust type for CN stocks: 'qfq'=forward, 'hfq'=backward, ''=none (US stocks ignore this)"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str, info) -> str:
        """Validate stock symbol format."""
        v = v.strip().upper()

        # Get market from context if available
        market = info.data.get("market") if hasattr(info, "data") else None

        if market == "cn":
            # A股代码：6位数字
            if not v.isdigit() or len(v) != 6:
                raise ValueError(
                    "CN stock symbol must be 6 digits (e.g., '600000', '000001')"
                )
        elif market == "us":
            # 美股代码：1-5个字母
            if not v.isalpha() or len(v) > 5:
                raise ValueError(
                    "US stock symbol must be 1-5 letters (e.g., 'AAPL', 'MSFT')"
                )

        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")
        return v

    def validate_date_range(self):
        """Validate start_date <= end_date."""
        start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        if start > end:
            raise ValueError("start_date must be <= end_date")

        if end > date.today():
            raise ValueError("end_date cannot be in the future")

        # 最多查询5年数据
        days_diff = (end - start).days
        if days_diff > 365 * 5:
            raise ValueError("Date range cannot exceed 5 years")


@router.post("/history")
def get_stock_history(req: StockHistoryRequest):
    """
    Get stock historical K-line data (query or save to database).

    **Request Body:**
    - market: "cn" (A-share) or "us" (US stock)
    - symbol: Stock code (e.g., "600000" for CN, "AAPL" for US)
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - action: "query" (return data) or "save" (save to database)
    - adjust: Adjust type for CN stocks (default: "qfq")

    **Response:**
    - status: "ok" or "error"
    - market: Market type
    - symbol: Stock symbol
    - count: Number of records
    - data: List of K-line data (if action="query")
    - message: Success/error message

    **Example:**
    ```json
    {
        "market": "cn",
        "symbol": "600000",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "action": "query"
    }
    ```
    """
    try:
        # Validate date range
        req.validate_date_range()

        # Import provider
        from data_sources.stock_history_provider import StockHistoryProvider

        provider = StockHistoryProvider()

        # Fetch data based on market
        if req.market == "cn":
            data = provider.get_cn_stock_history(
                symbol=req.symbol,
                start_date=req.start_date,
                end_date=req.end_date,
                adjust=req.adjust or "qfq"
            )
        else:  # us
            data = provider.get_us_stock_history(
                symbol=req.symbol,
                start_date=req.start_date,
                end_date=req.end_date
            )

        if data is None or len(data) == 0:
            return {
                "status": "error",
                "market": req.market,
                "symbol": req.symbol,
                "message": f"No data found for {req.market.upper()} stock {req.symbol}"
            }

        # Handle action
        if req.action == "save":
            # Save to database in background
            def _save():
                try:
                    # Get stock name from first record (if available)
                    name = data[0].get("name", req.symbol)

                    if req.market == "cn":
                        count = provider.save_cn_stock_to_db(req.symbol, name, data)
                    else:
                        count = provider.save_us_stock_to_db(req.symbol, name, data)

                    logger.info(f"Saved {count} records for {req.market.upper()} stock {req.symbol}")
                except Exception as e:
                    logger.error(f"Failed to save {req.market.upper()} stock {req.symbol}: {e}")

            Thread(target=_save, daemon=True).start()

            return {
                "status": "ok",
                "market": req.market,
                "symbol": req.symbol,
                "count": len(data),
                "message": f"Saving {len(data)} records to database in background"
            }

        else:  # query
            return {
                "status": "ok",
                "market": req.market,
                "symbol": req.symbol,
                "count": len(data),
                "data": data,
                "message": f"Successfully fetched {len(data)} records"
            }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get stock history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history/{market}/{symbol}")
def get_stock_history_simple(
    market: Literal["cn", "us"],
    symbol: str,
    start_date: str,
    end_date: str,
    adjust: str = "qfq"
):
    """
    Get stock historical data (simplified GET endpoint).

    **Path Parameters:**
    - market: "cn" or "us"
    - symbol: Stock code

    **Query Parameters:**
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - adjust: Adjust type for CN stocks (default: "qfq")

    **Example:**
    ```
    GET /api/market/stock/history/cn/600000?start_date=2024-01-01&end_date=2024-12-31
    ```
    """
    req = StockHistoryRequest(
        market=market,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        action="query",
        adjust=adjust
    )

    return get_stock_history(req)
