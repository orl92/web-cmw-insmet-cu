"""Safe cache helpers for the Redis-backed caching layer (change 003-cache-redis).

These wrappers degrade gracefully: if the configured cache backend raises a
connection error (e.g. Redis is unreachable while ``USE_REDIS_CACHE=True``), the
read is treated as a miss and the write is skipped instead of bubbling up a 500.

The ``redis`` package is imported lazily so this module can be imported in
environments where Redis is not installed (dev/CI run with LocMemCache).
"""

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def _cache_failure_exceptions():
    """Return the exception types that mean "cache backend is unavailable".

    Lazy-import ``redis.exceptions`` so this module loads even when the ``redis``
    package is not installed (the default LocMemCache path never needs it).
    """
    try:
        from redis.exceptions import RedisError

        return (RedisError, ConnectionError, OSError)
    except ImportError:  # pragma: no cover - redis not installed
        return (ConnectionError, OSError)


def safe_cache_get(key, default=None):
    """``cache.get`` that degrades to ``default`` on a backend failure."""
    try:
        return cache.get(key, default)
    except _cache_failure_exceptions() as exc:
        logger.warning('Cache GET failed for %s; serving uncached. %s', key, exc)
        return default


def safe_cache_set(key, value, timeout):
    """``cache.set`` that silently skips the write on a backend failure."""
    try:
        cache.set(key, value, timeout)
    except _cache_failure_exceptions() as exc:
        logger.warning('Cache SET failed for %s; skipping write. %s', key, exc)


def build_api_cache_key(request):
    """Build a stable cache key for a read-only API request.

    Key format: ``api:{request.path}:{normalized_sorted_query_string}``.
    The query string is normalized (keys and values sorted) so that two requests
    differing only in query-param order resolve to the same key, while distinct
    param values resolve to distinct keys.
    """
    items = []
    for key in sorted(request.GET):
        for value in sorted(request.GET.getlist(key)):
            items.append(f'{key}={value}')
    normalized = '&'.join(items)
    if normalized:
        return f'api:{request.path}:{normalized}'
    return f'api:{request.path}:'
