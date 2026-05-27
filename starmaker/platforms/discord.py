"""Discord message draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig

# Named emoji / symbol constants so the source stays legible (raw escapes hidden).
LINK = "\U0001f517"  # 🔗
PRAY = "\U0001f64f"  # 🙏
BULLET = "•"  # • (U+2022)
EM_DASH = "—"  # —

# Maps a project tag (lowercased) to relevant Discord communities. Kept inline
# (not in config) because it is a curated mapping of ecosystem tags to known
# servers, not user-tunable state.
TAG_SERVERS: dict[str, list[str]] = {
    "rust": ["Rust Programming Language", "Rust Community"],
    "python": ["Python Discord", "Python"],
    "typescript": ["TypeScript Community"],
    "javascript": ["Reactiflux", "JavaScript"],
    "react": ["Reactiflux"],
    "tauri": ["Tauri"],
    "linux": ["Linux", "r/Linux"],
    "go": ["Gophers"],
}


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate a Discord message draft for community showcase channels.

    Returns a single-entry mapping (``discord.md``). The output keeps the
    ``**Post this in #showcase ...**`` marker that :mod:`starmaker.commands.post`
    uses to extract the message body.
    """
    proj = config.project
    highlights_md = "\n".join(f"{BULLET} {h}" for h in proj.highlights) if proj.highlights else ""
    tech_md = ", ".join(proj.tech_stack) if proj.tech_stack else ""

    # Suggested Discord servers based on the project's tags.
    suggested: set[str] = set()
    for tag in proj.tags:
        for server in TAG_SERVERS.get(tag.lower(), []):
            suggested.add(server)
    suggested.add("Open Source")

    message = f"""**{proj.name}** {EM_DASH} {proj.tagline}

{proj.description}

**Highlights:**
{highlights_md}

{"**Built with:** " + tech_md if tech_md else ""}

{LINK} **GitHub:** <{proj.repo}>
{"**Website:** <" + proj.website + ">" if proj.website else ""}

Feedback welcome! {PRAY}"""

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
