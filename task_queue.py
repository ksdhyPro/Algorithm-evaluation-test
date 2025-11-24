import json
import os
import threading
from datetime import datetime

QUEUE_FILE = './task_queue.json'
_queue_lock = threading.Lock()


def _load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_queue(queue):
    os.makedirs(os.path.dirname(QUEUE_FILE) or '.', exist_ok=True)
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def enqueue_task(task):
    with _queue_lock:
        queue = _load_queue()
        task['enqueued_at'] = datetime.utcnow().isoformat()
        queue.append(task)
        _save_queue(queue)
        # 返回当前队列长度（包含本任务）
        return len(queue)


def dequeue_task():
    with _queue_lock:
        queue = _load_queue()
        if not queue:
            return None
        task = queue.pop(0)
        _save_queue(queue)
        return task


def peek_queue():
    with _queue_lock:
        return list(_load_queue())


def queue_size():
    with _queue_lock:
        return len(_load_queue())

