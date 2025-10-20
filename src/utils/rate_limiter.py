from time import time
from collections import defaultdict, deque


class SimpleRateLimiter:
    """Limitador por usuario con ventana móvil de 60 segundos.

    allow(user_id, per_minute) -> True si puede pasar, False si excede.
    """

    def __init__(self):
        self._events = defaultdict(deque)

    def allow(self, user_id: str, per_minute: int) -> bool:
        now = time()
        window_start = now - 60
        q = self._events[user_id]
        # limpiar eventos fuera de ventana
        while q and q[0] < window_start:
            q.popleft()
        if len(q) >= per_minute:
            return False
        q.append(now)
        return True
