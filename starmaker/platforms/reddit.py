"""Reddit post draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate Reddit post drafts for configured subreddits."""
    proj = config.project
    subreddits = config.promotion.reddit.get("subreddits", [
        "opensource", "commandline", "programming",
    ])
    # Add tag-based subreddits
    tag_subs = {
        "python": "Python",
        "rust": "rust",
        "go": "golang",
        "javascript": "javascript",
        "typescript": "typescript",
        "react": "reactjs",
        "linux": "linux",
        "macos": "macapps",
    }
    for tag in proj.tags:
        sub = tag_subs.get(tag.lower())
        if sub and sub not in subreddits:
            subreddits.append(sub)

    highlights_md = "\n".join(f"- {h}" for h in proj.highlights) if proj.highlights else ""
    tech_md = ", ".join(proj.tech_stack) if proj.tech_stack else ""
    tags_md = " ".join(f"`{t}`" for t in proj.tags) if proj.tags else ""

    drafts = {}
    for sub in subreddits:
        title = f"I built {proj.name} — {proj.tagline}"
        if len(title) > 300:
            title = title[:297] + "..."

        body = f"""Hey r/{sub}!

I've been working on **{proj.name}** — {proj.tagline}.

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
    """Get license name, defaulting to MIT."""
    return "MIT"
