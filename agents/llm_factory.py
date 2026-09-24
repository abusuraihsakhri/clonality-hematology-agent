"""Deterministic query adapter retained for legacy compatibility."""

from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Clonality Hematology Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} deterministic adapter] "
            "Only the local mock provider is implemented. "
            f"Query received: '{prompt[:80]}'."
        )


class LLMFactory:
    """Create the implemented local deterministic adapter."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Clonality Hematology Agent"):
        normalized = str(provider).lower()
        if normalized in {"mock", "deterministic", "test"}:
            return MockLLM(system_name)
        raise ValueError(f"Provider '{provider}' is not implemented. Use provider='mock'.")
