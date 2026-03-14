"""Reddit r/wallstreetbets sentiment connector."""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import requests


def count_ticker_mentions(posts: list[dict], tickers: list[str]) -> dict[str, int]:
    """Count how many posts mention each ticker (case-sensitive, word boundary)."""
    counts = {t: 0 for t in tickers}
    for post in posts:
        title = post.get("title", "")
        for ticker in tickers:
            if re.search(rf"\b{re.escape(ticker)}\b", title):
                counts[ticker] += 1
    return counts


class RedditSource:
    """Fetches post titles from r/wallstreetbets and counts ticker mentions."""

    BASE_URL = "https://www.reddit.com/r/wallstreetbets/new.json"

    def fetch_mentions(
        self,
        tickers: list[str],
        limit: int = 100,
    ) -> pd.DataFrame:
        """Fetch recent WSB posts and return daily ticker mention counts."""
        resp = requests.get(
            self.BASE_URL,
            params={"limit": limit},
            headers={"User-Agent": "bigshort-research/0.1"},
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])

        daily_posts: dict[str, list[dict]] = {}
        for child in children:
            post = child.get("data", child)
            ts = post.get("created_utc", 0)
            date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
            daily_posts.setdefault(date_str, []).append(post)

        rows = []
        for date_str, posts in sorted(daily_posts.items()):
            counts = count_ticker_mentions(posts, tickers)
            counts["date"] = pd.Timestamp(date_str)
            rows.append(counts)

        if not rows:
            df = pd.DataFrame(columns=["date"] + tickers)
        else:
            df = pd.DataFrame(rows)

        return df.set_index("date")
