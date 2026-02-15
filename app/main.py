"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    # Initialize database tables
    try:
        from data_crawler.db.init_tables import init_all_tables
        init_all_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error("Failed to initialize database tables: %s", e)

    # Start scheduler
    from app.scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()
    logger.info("Scheduler started")

    yield

    # Shutdown scheduler
    shutdown_scheduler()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="FinancialMarketWatchdog",
    description="Investment monitoring and data crawling web service",
    version="2.0.0",
    lifespan=lifespan,
)

# Register routers
from app.routers import system, market, crawler, analysis  # noqa: E402

app.include_router(system.router)
app.include_router(market.router)
app.include_router(crawler.router)
app.include_router(analysis.router)
