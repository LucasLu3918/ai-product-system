"""Compatibility exports for the shared Runtime Context path resolver."""

import runtime_context as _runtime

fallback_home = _runtime.fallback_home
trusted_fallback = _runtime.trusted_fallback
writable = _runtime.writable
def private_fallback():
    return _runtime.private_fallback(fallback_home_fn=fallback_home, trusted_fallback_fn=trusted_fallback)


def _overrides() -> dict[str, object]:
    return {
        "fallback_home_fn": fallback_home,
        "trusted_fallback_fn": trusted_fallback,
        "writable_fn": writable,
        "private_fallback_fn": private_fallback,
    }


def cache_home(env=None, *, for_write=False, namespace="aips"):
    return _runtime.cache_home(env, for_write=for_write, namespace=namespace, **_overrides())


def cache_environment(env=None):
    return _runtime.cache_environment(env, **_overrides())

__all__ = ["fallback_home", "trusted_fallback", "writable", "private_fallback", "cache_home", "cache_environment"]
