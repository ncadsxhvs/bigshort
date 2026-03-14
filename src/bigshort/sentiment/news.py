"""NewsAPI connector for Fedspeak hawkishness scoring."""

from __future__ import annotations

import os

import pandas as pd
import requests

HAWK_KEYWORDS = {"hike", "tighten", "tightening", "hawkish", "inflation", "elevated", "persistent", "restrictive"}
DOVE_KEYWORDS = {"cut", "easing", "dovish", "stimulus", "accommodate", "accommodative", "pause", "pivot"}


def score_hawkishness(articles: list[dict]) -> float:
    """Score a batch of articles: +1 per hawk keyword, -1 per dove keyword, averaged."""
    if not articles:
        return 0.0
    total = 0.0
    for article in articles:
        text = article.get("title", "").lower()
        total += sum(1 for kw in HAWK_KEYWORDS if kw in text)
        total -= sum(1 for kw in DOVE_KEYWORDS if kw in text)
    return total / len(articles)


class NewsSource:
    """Fetches Fed-related news from NewsAPI and scores hawkishness."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.environ.get("NEWSAPI_KEY", "")
        if not self._key:
            raise RuntimeError(
                "NEWSAPI_KEY required. Set the NEWSAPI_KEY environment variable "
                "or pass api_key= to NewsSource()."
            )

    def fetch_fedspeak(self, start: str, end: str) -> pd.DataFrame:
        """Fetch Fed-related articles and return daily hawkishness scores."""
        resp = requests.get(
            self.BASE_URL,
            params={
                "q": "Federal Reserve OR FOMC OR Fed rate",
                "from": start,
                "to": end,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 100,
                "apiKey": self._key,
            },
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])

        daily: dict[str, list[dict]] = {}
        for a in articles:
            date_str = a["publishedAt"][:10]
            daily.setdefault(date_str, []).append(a)

        rows = []
        for date_str, day_articles in sorted(daily.items()):
            rows.append({"date": pd.Timestamp(date_str), "hawkishness": score_hawkishness(day_articles)})

        if not rows:
            return pd.DataFrame(columns=["hawkishness"]).rename_axis("date")

        df = pd.DataFrame(rows).set_index("date")
        return df
