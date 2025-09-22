import time
from typing import Any, Dict, List, Optional
from collections import deque

_message_statuses: Dict[str, List[Dict[str, Any]]] = {}
_recent: deque = deque(maxlen=200)

def add_status(message_id: str, status: str, payload: Dict[str, Any]) -> None:
    ts = time.time()
    entry = {'status': status, 'timestamp': ts, 'payload': payload}
    if message_id not in _message_statuses:
        _message_statuses[message_id] = []
    _message_statuses[message_id].append(entry)
    _recent.appendleft({'message_id': message_id, **entry})

def get_status_by_message_id(message_id: str) -> Optional[Dict[str, Any]]:
    items = _message_statuses.get(message_id)
    if items is None:
        return
    return {'message_id': message_id, 'events': items}

def list_recent_statuses(limit: int=50) -> List[Dict[str, Any]]:
    return list(list(_recent)[:max(1, min(limit, 200))])