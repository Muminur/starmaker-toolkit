"""Discord message draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate Discord message drafts for community showcase channels."""
    proj = config.project
    highlights_md = "\n".join(f"\u2022 {h}" for h in proj.highlights) if proj.highlights else ""
    tech_md = ", ".join(proj.tech_stack) if proj.tech_stack else ""

    # Suggested Discord servers based on tags
    tag_servers = {
        "rust": ["Rust Programming Language", "Rust Community"],
        "python": ["Python Discord", "Python"],
        "typescript": ["TypeScript Community"],
        "javascript": ["Reactiflux", "JavaScript"],
        "react": ["Reactiflux"],
        "tauri": ["Tauri"],
        "linux": ["Linux", "r/Linux"],
        "go": ["Gophers"],
    }

    suggested = set()
    for tag in proj.tags:
        for server in tag_servers.get(tag.lower(), []):
            suggested.add(server)
    suggested.add("Open Source")

    message = f"""**{proj.name}** \u2014 {proj.tagline}

{proj.description}

**Highlights:**
{highlights_md}

{"**Built with:** " + tech_md if tech_md else ""}

\U0001f517 **GitHub:** <{proj.repo}>
{"**Website:** <" + proj.website + ">" if proj.website else ""}

Feedback welcome! \U0001f64f"""

    servers_list = "\n".join(f"- {s}" for s in sorted(suggested))

    draft = f"""# Discord Message

**Post this in #showcase or #projects channels:**

{message}

---

## Suggested Discord Servers:
{servers_list}

## Discord Tips:
- Find the #showcase, #projects, or #share-your-work channel
- Read channel rules first — some require specific formats
- Include a screenshot or GIF
- Be active in the community before and after posting
- Don't spam multiple channels in the same server
- Respond to questions and feedback promptly
"""

    return {"discord.md": draft}
