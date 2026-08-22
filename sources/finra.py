# sources/finra.py
from core.base_source import BaseSource, register_source

@register_source
class FinraSource(BaseSource):
    name = "finra"

    def fetch(self, ticker: str) -> list[dict]:
        # ... download short interest ...
        return [{"ticker": ticker, "metric": "short_interest",
                 "period": "2026-08-15", "period_type": "point",
                 "value": 12.4, "unit": "pct", "source": "finra"}]
