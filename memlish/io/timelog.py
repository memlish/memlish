import time
import datetime
from memlish.config import ESTag, DEBUG_MODE


def log_duration(func):
    def wrapper(*args, **kwargs):
        if not DEBUG_MODE:
            return func(*args, **kwargs)
        else:
            start = time.time()
            return_value = func(*args, **kwargs)
            end = time.time()
            print({
                "es_tag": ESTag.TIMELOG,
                "timestamp": str(datetime.datetime.utcnow()),
                "function": f"{func.__module__}.{func.__name__}",
                "duration": end-start
            })
            return return_value

    return wrapper
