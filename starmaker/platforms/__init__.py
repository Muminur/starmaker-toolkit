"""Platform-specific post template generators."""

from __future__ import annotations

from starmaker.platforms.reddit import generate as reddit_generate
from starmaker.platforms.hackernews import generate as hackernews_generate
from starmaker.platforms.devto import generate as devto_generate
from starmaker.platforms.twitter import generate as twitter_generate
from starmaker.platforms.discord import generate as discord_generate

PLATFORMS = {
    "reddit": reddit_generate,
    "hackernews": hackernews_generate,
    "devto": devto_generate,
    "twitter": twitter_generate,
    "discord": discord_generate,
}
