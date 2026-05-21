"""Detect common crawlers and SEO bots by User-Agent."""

from __future__ import annotations

BOT_SIGNATURES: tuple[str, ...] = (
    "googlebot",
    "bingbot",
    "yandexbot",
    "duckduckbot",
    "ahrefsbot",
    "semrushbot",
    "mj12bot",
    "petalbot",
    "bytespider",
    "facebookexternalhit",
    "twitterbot",
)


def is_bot(user_agent: str | None) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(signature in ua for signature in BOT_SIGNATURES)
