import time
from collections import OrderedDict

# LRU cache with max size and TTL
MAX_CACHE_SIZE = 1000
CACHE_TTL_SECONDS = 3600  # 1 hour


class CacheStore:
    def __init__(self, max_size=MAX_CACHE_SIZE, ttl=CACHE_TTL_SECONDS):
        self.max_size = max_size
        self.ttl = ttl
        self._store = OrderedDict()
        self._timestamps = {}

    def __contains__(self, key):
        if key not in self._store:
            return False

        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl:
            self._evict(key)
            return False

        # Move to end (LRU)
        self._store.move_to_end(key)
        return True

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return self._store[key]

    def __setitem__(self, key, value):
        # Evict oldest if at capacity
        if key not in self._store and len(self._store) >= self.max_size:
            oldest = next(iter(self._store))
            self._evict(oldest)

        self._store[key] = value
        self._timestamps[key] = time.time()
        self._store.move_to_end(key)

    def _evict(self, key):
        if key in self._store:
            del self._store[key]
        if key in self._timestamps:
            del self._timestamps[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        self._store.clear()
        self._timestamps.clear()


cache_store = CacheStore()
