"""Platform publishers for posting content via official APIs."""

from __future__ import annotations

from starmaker.publishers.reddit_publisher import RedditPublisher
from starmaker.publishers.hackernews_publisher import HackerNewsPublisher
from starmaker.publishers.devto_publisher import DevtoPublisher
from starmaker.publishers.twitter_publisher import TwitterPublisher
from starmaker.publishers.discord_publisher import DiscordPublisher

PUBLISHERS = {
    "reddit": RedditPublisher,
    "hackernews": HackerNewsPublisher,
    "devto": DevtoPublisher,
    "twitter": TwitterPublisher,
    "discord": DiscordPublisher,
}
