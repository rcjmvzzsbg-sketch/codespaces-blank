# core/base_source.py
from abc import ABC, abstractmethod

class BaseSource(ABC):
    name: str = "unnamed"          # e.g. "edgar"
    enabled: bool = True

    @abstractmethod
    def fetch(self, ticker: str) -> list[dict]:
        """Return a list of fact dicts:
        {ticker, metric, period, period_type, value, unit, source}"""
        ...

# Registry that auto-collects subclasses
SOURCES: dict[str, BaseSource] = {}

def register_source(cls):
    """Class decorator — a source registers itself just by existing."""
    SOURCES[cls.name] = cls()
    return cls
