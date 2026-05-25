"""Twitter/X post draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig

# Named emoji / symbol constants so the source stays legible (raw escapes hidden).
ROCKET = "\U0001f680"  # 🚀
STAR = "⭐"  # ⭐
HEART = "❤️"  # ❤️ (heart + variation selector)
THREAD = "\U0001f9f5"  # 🧵
DOWN_ARROW = "↓"  # ↓
TRIANGLE_RIGHT = "▷"  # ▷ (was chr(9655))
EM_DASH = "—"  # —


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate Twitter/X drafts as a thread and a single-tweet variant.

    Returns a mapping with ``twitter_thread.md`` and ``twitter_single.md``. The
    single-tweet draft keeps its ``# `` heading and trailing ``---`` separator so
    that :mod:`starmaker.commands.post` extracts the tweet body correctly.
    """
    proj = config.project
    hashtags = " ".join(f"#{t}" for t in proj.tags[:5]) if proj.tags else "#opensource"

    # Single tweet version
    single = f"""{ROCKET} Introducing {proj.name} {EM_DASH} {proj.tagline}

{proj.highlights[0] if proj.highlights else proj.description[:100]}

{proj.repo}

{hashtags}"""

    # Thread version
    highlights_tweets = ""
    for i, h in enumerate(proj.highlights[:5], 1):
        highlights_tweets += f"""
---

**Tweet {i + 1}:**

{TRIANGLE_RIGHT} {h}

"""

    thread = f"""# Twitter/X Thread

**Tweet 1 (Hook):**

{ROCKET} I just open-sourced {proj.name}!

{proj.tagline}

Here's what it does and why I built it {THREAD}{DOWN_ARROW}
{highlights_tweets}
---

**Final Tweet (CTA):**

{proj.name} is free and open-source {HEART}

{STAR} Star on GitHub: {proj.repo}
{"Follow me for updates: @" + config.author.twitter if config.author.twitter else ""}

{hashtags}

---

## Twitter Tips:
- Include a GIF/video demo in Tweet 1 for 3-5x engagement
- Post between 9-11 AM or 1-3 PM your audience's timezone
- Quote-tweet yourself to bump visibility
- Reply to your own thread with additional context
- Tag relevant accounts (framework authors, community accounts)
"""

    single_draft = f"""# Twitter/X Single Post

{single}

---
*Keep under 280 characters. Add a screenshot or GIF for engagement.*
"""

    return {
        "twitter_thread.md": thread,
        "twitter_single.md": single_draft,
    }
