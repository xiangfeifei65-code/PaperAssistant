import time
from functools import wraps
from src.utils.logger import logger
from src.utils.config import config

def retry_on_exception(max_retries=None, delay=None):
    if max_retries is None:
        max_retries = config.MAX_RETRIES
    if delay is None:
        delay = config.RETRY_DELAY

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}"
                    )
                    if attempt < max_retries:
                        time.sleep(delay * attempt)  # 指数退避
            raise RuntimeError(
                f"Function {func.__name__} failed after {max_retries} attempts"
            ) from last_exception
        return wrapper
    return decorator