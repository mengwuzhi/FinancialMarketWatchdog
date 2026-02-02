import logging
from functools import wraps
from typing import Callable, Optional

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

from core.trading_calendar import TradingCalendar
from notifiers.dingtalk import DingTalkNotifier

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""

    def __init__(self, timezone: str = "Asia/Shanghai"):
        executors = {"default": ThreadPoolExecutor(10)}
        self.scheduler = BlockingScheduler(executors=executors, timezone=timezone)
        self.trading_calendar = TradingCalendar()
        self.notifier: Optional[DingTalkNotifier] = None

    def set_notifier(self, notifier: DingTalkNotifier):
        """设置通知器，用于错误通知"""
        self.notifier = notifier

    def add_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        trading_day_only: bool = False,
        **trigger_args,
    ):
        """
        添加定时任务

        Args:
            func: 任务函数
            trigger: 触发器类型（cron, interval等）
            job_id: 任务ID
            trading_day_only: 是否仅在交易日执行
            **trigger_args: 触发器参数
        """
        # 包装任务函数
        wrapped_func = self._job_wrapper(func, job_id, trading_day_only)

        # 添加到调度器
        self.scheduler.add_job(
            wrapped_func, trigger=trigger, id=job_id, **trigger_args
        )
        logger.info(f"Job added: {job_id}")

    def _job_wrapper(
        self, func: Callable, job_id: str, trading_day_only: bool
    ) -> Callable:
        """
        任务包装器，添加交易日检查和错误处理

        Args:
            func: 原始函数
            job_id: 任务ID
            trading_day_only: 是否仅在交易日执行

        Returns:
            包装后的函数
        """

        @wraps(func)
        def wrapped():
            # 检查交易日
            if trading_day_only:
                if not self.trading_calendar.is_a_share_trading_day():
                    logger.info(f"Skipped {job_id}: not a trading day")
                    return

            # 执行任务
            try:
                logger.info(f"Running job: {job_id}")
                func()
                logger.info(f"Job completed: {job_id}")
            except Exception as e:
                error_msg = f"Job {job_id} failed: {str(e)}"
                logger.error(error_msg, exc_info=True)

                # 发送错误通知
                if self.notifier:
                    try:
                        self.notifier.send_text(
                            f"系统错误提醒\n\n任务: {job_id}\n错误: {str(e)}"
                        )
                    except Exception as notify_error:
                        logger.error(
                            f"Failed to send error notification: {notify_error}"
                        )

        return wrapped

    def start(self):
        """启动调度器"""
        logger.info("Starting scheduler...")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            raise

    def shutdown(self):
        """停止调度器"""
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown()


def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
