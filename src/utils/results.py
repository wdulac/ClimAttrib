from .redis_cache import get_cache
from .tasks import attribution

def get_result(result_id):

    if result_id.startswith("TASK:"):
        task_id = result_id.split(":", 1)[1]
        task = attribution.AsyncResult(task_id)
        if task.ready():
            return task.result
        else:
            return None

    elif result_id.startswith("CACHE:"):
        cache_key = result_id.split(":", 1)[1]
        return get_cache(cache_key)

    else:
        raise ValueError("Invalid result_id")