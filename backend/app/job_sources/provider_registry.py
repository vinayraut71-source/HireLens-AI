"""
Provider Registry — dynamically tracks and manages active job ingestion providers.
Sprint 13: Framework.
"""
from app.job_sources.providers import PROVIDER_REGISTRY


class ProviderRegistry:
    # Class-level state tracking (in-memory config)
    _states: dict[str, bool] = {name: True for name in PROVIDER_REGISTRY.keys()}

    @classmethod
    def register_provider(cls, name: str, provider_instance) -> None:
        """
        Dynamically register a new provider to the framework.
        """
        name_clean = name.lower().strip()
        PROVIDER_REGISTRY[name_clean] = provider_instance
        cls._states[name_clean] = True

    @classmethod
    def unregister_provider(cls, name: str) -> None:
        """
        Dynamically unregister a provider from the framework.
        """
        name_clean = name.lower().strip()
        if name_clean in PROVIDER_REGISTRY:
            del PROVIDER_REGISTRY[name_clean]
        if name_clean in cls._states:
            del cls._states[name_clean]

    @classmethod
    def enable_provider(cls, name: str) -> None:
        """
        Enables an ingestion provider source.
        """
        name_clean = name.lower().strip()
        if name_clean in PROVIDER_REGISTRY:
            cls._states[name_clean] = True

    @classmethod
    def disable_provider(cls, name: str) -> None:
        """
        Disables an ingestion provider source.
        """
        name_clean = name.lower().strip()
        if name_clean in PROVIDER_REGISTRY:
            cls._states[name_clean] = False

    @classmethod
    def is_enabled(cls, name: str) -> bool:
        """
        Checks if a provider is currently enabled.
        """
        return cls._states.get(name.lower().strip(), False)

    @classmethod
    def get_provider(cls, name: str):
        """
        Retrieves a registered provider instance.
        """
        return PROVIDER_REGISTRY.get(name.lower().strip())

    @classmethod
    def list_providers(cls) -> list[dict]:
        """
        List all registered providers and their configuration status.
        """
        return [
            {"name": name, "enabled": cls._states.get(name, False)}
            for name in PROVIDER_REGISTRY.keys()
        ]
