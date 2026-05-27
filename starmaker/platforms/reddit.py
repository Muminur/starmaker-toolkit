"""Reddit post draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig

# Em dash separator used in titles and prose (U+2014).
EM_DASH = "—"

# Maps a project tag (lowercased) to its most relevant subreddit. This data is
# intentionally kept inline rather than in config: it is a curated, opinionated
# mapping of common ecosystem tags to active subreddits, not user-tunable state.
TAG_SUBREDDITS: dict[str, str] = {
    "python": "Python",
    "rust": "rust",
    "go": "golang",
    "javascript": "javascript",
    "typescript": "typescript",
    "react": "reactjs",
    "linux": "linux",
    "macos": "macapps",
}


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate Reddit post drafts for configured and tag-derived subreddits.

    Returns a mapping of draft filename (``reddit_r_<sub>.md``) to its markdown
    content. The content preserves the ``**Title:**`` and ``**Body:**`` markers
    that :mod:`starmaker.commands.post` relies on when parsing drafts back.
    """
    proj = config.project
    subreddits: list[str] = config.promotion.reddit.get("subreddits", [
        "opensource", "commandline", "programming",
    ])
    # Add tag-based subreddits derived from the project's tags.
    for tag in proj.tags:
        sub = TAG_SUBREDDITS.get(tag.lower())
        if sub and sub not in subreddits:
            subreddits.append(sub)

    highlights_md = "\n".join(f"- {h}" for h in proj.highlights) if proj.highlights else ""
    tech_md = ", ".join(proj.tech_stack) if proj.tech_stack else ""
    tags_md = " ".join(f"`{t}`" for t in proj.tags) if proj.tags else ""

    drafts: dict[str, str] = {}
    for sub in subreddits:
        title = f"I built {proj.name} {EM_DASH} {proj.tagline}"
        if len(title) > 300:
            title = title[:297] + "..."

        body = f"""Hey r/{sub}!

I've been working on **{proj.name}** {EM_DASH} {proj.tagline}.

{proj.description}

**Key highlights:**
{highlights_md}

{"**Built with:** " + tech_md if tech_md else ""}

{"**Tags:** " + tags_md if tags_md else ""}

**Links:**
- GitHub: {proj.repo}
{"- Website: " + proj.website if proj.website else ""}

I'd love to hear your feedback! If you find it useful, a star on GitHub would mean a lot.

---
*{proj.name} is free and open-source under the {_get_license_text(config)} license.*"""

        drafts[f"reddit_r_{sub}.md"] = f"# Reddit Post for r/{sub}\n\n**Title:** {title}\n\n**Body:**\n\n{body}"

    return drafts


def _get_license_text(config: StarMakerConfig) -> str:
    """Return the project license name from config, defaulting to ``MIT``.

    Reads the optional ``license`` field from the project config. The current
    :class:`~starmaker.config.ProjectConfig` may not define it, so this uses
    :func:`getattr` to stay forward-compatible: if a ``license`` field is added
    later it is picked up automatically, otherwise it falls back to ``MIT``.
    """
    license_name = getattr(config.project, "license", None)
    return license_name or "MIT"
