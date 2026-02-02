"""重试机制工具"""

import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 5.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None,
):
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数（指数退避）
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数

    Example:
        @retry_on_failure(max_attempts=3, delay=5)
        def fetch_data():
            return requests.get("https://api.example.com")
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}"
                    )
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")

                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(f"Retry callback error: {callback_error}")

                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def retry_with_timeout(
    max_attempts: int = 3,
    timeout: float = 30.0,
    delay: float = 5.0,
):
    """
    带超时的重试装饰器（针对网络请求）

    Args:
        max_attempts: 最大尝试次数
        timeout: 请求超时时间（秒）
        delay: 重试延迟（秒）

    Example:
        @retry_with_timeout(max_attempts=3, timeout=30)
        def fetch_lof_data():
            return ak.fund_lof_spot_em()
    """
    import requests

    return retry_on_failure(
        max_attempts=max_attempts,
        delay=delay,
        exceptions=(
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
        ),
    )
