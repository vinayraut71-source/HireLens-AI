"""
Provider Rate Limiter — enforces per-source ingestion rate limits and backoffs.
Sprint 13: Framework.
"""
import time
import math


class ProviderRateLimiter:
    # In-memory registry to track rate limiting and cooldown state
    # Format: {provider_name: {"last_call_time": float, "attempts": int, "cooldown_until": float}}
    _states: dict[str, dict] = {}
    
    # Default rate limit config (min interval in seconds between runs)
    _min_intervals: dict[str, float] = {
        # Default minimum cooldown interval of 1 second for standard, can be customized
    }

    @classmethod
    def _get_state(cls, provider_name: str) -> dict:
        name_clean = provider_name.lower().strip()
        if name_clean not in cls._states:
            cls._states[name_clean] = {
                "last_call_time": 0.0,
                "attempts": 0,
                "cooldown_until": 0.0
            }
        return cls._states[name_clean]

    @classmethod
    async def check_rate_limit(cls, provider_name: str, db=None) -> bool:
        """
        Check if the provider is allowed to sync now.
        Returns True if allowed, False if rate-limited or in cooldown.
        """
        now = time.time()
        state = cls._get_state(provider_name)
        
        # Check explicit cooldown
        if now < state["cooldown_until"]:
            return False

        # Check minimum interval limit (default to 2.0 seconds minimum gap for testing)
        min_interval = cls._min_intervals.get(provider_name.lower().strip(), 2.0)
        if db:
            from app.job_sources.models import ProviderConfig
            config = await ProviderConfig.get_or_create(db, provider_name)
            if config and config.rate_limit_per_hour > 0:
                min_interval = 3600.0 / config.rate_limit_per_hour

        if now - state["last_call_time"] < min_interval:
            return False

        return True

    @classmethod
    async def get_retry_after(cls, provider_name: str, db=None) -> float:
        """
        Returns the number of seconds until a retry is allowed.
        """
        now = time.time()
        state = cls._get_state(provider_name)
        
        cooldown_wait = max(0.0, state["cooldown_until"] - now)
        if cooldown_wait > 0:
            return cooldown_wait

        min_interval = cls._min_intervals.get(provider_name.lower().strip(), 2.0)
        if db:
            from app.job_sources.models import ProviderConfig
            config = await ProviderConfig.get_or_create(db, provider_name)
            if config and config.rate_limit_per_hour > 0:
                min_interval = 3600.0 / config.rate_limit_per_hour

        interval_wait = max(0.0, min_interval - (now - state["last_call_time"]))
        return max(cooldown_wait, interval_wait)

    @classmethod
    def record_success(cls, provider_name: str) -> None:
        """
        Resets attempt counts and updates call timestamps.
        """
        state = cls._get_state(provider_name)
        state["last_call_time"] = time.time()
        state["attempts"] = 0
        state["cooldown_until"] = 0.0

    @classmethod
    def record_failure(cls, provider_name: str) -> None:
        """
        Increments attempts and applies exponential backoff cooldown.
        """
        state = cls._get_state(provider_name)
        state["last_call_time"] = time.time()
        state["attempts"] += 1
        
        # Calculate exponential backoff (e.g. 2, 4, 8, 16 seconds...)
        backoff = math.pow(2, state["attempts"])
        state["cooldown_until"] = time.time() + backoff
