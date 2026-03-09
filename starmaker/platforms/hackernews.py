"""Hacker News post draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate a Hacker News Show HN post draft."""
    proj = config.project

    title = f"Show HN: {proj.name} \u2013 {proj.tagline}"
    if len(title) > 80:
        title = title[:77] + "..."

    highlights_text = "\n".join(f"- {h}" for h in proj.highlights) if proj.highlights else ""
    tech_text = ", ".join(proj.tech_stack) if proj.tech_stack else ""

    # HN posts are URL submissions, but Show HN can have text
    body = f"""{proj.description}

{("Key features:" + chr(10) + highlights_text) if highlights_text else ""}

{"Tech stack: " + tech_text if tech_text else ""}

GitHub: {proj.repo}
{"Website: " + proj.website if proj.website else ""}

Would love feedback from the HN community!"""

    draft = f"""# Hacker News — Show HN Post

**Title:** {title}

**URL:** {proj.repo}

**Text (optional, for Show HN):**

{body}

---

## Tips for HN:
- Post between 9-11 AM ET (weekdays) for best visibility
- Title should be factual, not salesy
- Respond to every comment promptly
- Don't ask for upvotes
- Be ready to explain technical decisions
"""

    return {"hackernews.md": draft}
