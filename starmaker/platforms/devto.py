"""Dev.to article draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig

# Named symbol constants so the source stays legible (raw escapes hidden).
STAR = "⭐"  # ⭐
EM_DASH = "—"  # —
NEWLINE = "\n"


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate a Dev.to article draft.

    Returns a single-entry mapping (``devto_article.md``). The output keeps its
    YAML frontmatter (``title:`` and ``tags:``) and ``## Dev.to Publishing Tips``
    section so :mod:`starmaker.commands.post` can parse the title, tags and body.
    """
    proj = config.project
    tags_str = ", ".join(proj.tags[:4]) if proj.tags else "opensource"
    highlights_md = "\n".join(f"- {h}" for h in proj.highlights) if proj.highlights else ""
    tech_md = ", ".join(proj.tech_stack) if proj.tech_stack else ""

    article = f"""---
title: "Introducing {proj.name}: {proj.tagline}"
published: false
tags: {tags_str}
cover_image: ""
---

## What is {proj.name}?

{proj.description}

## Why I Built This

<!-- Tell your story here — what problem were you solving? What frustrated you about existing tools? -->

I was looking for a tool that [describe the problem]. Existing solutions like {", ".join(proj.competitors[:3]) if proj.competitors else "alternatives"} didn't quite fit because [reasons].

So I built **{proj.name}**.

## Key Features

{highlights_md}

{"## Tech Stack" + NEWLINE + NEWLINE + tech_md if tech_md else ""}

<!-- Add a paragraph about interesting technical decisions -->

## Getting Started

```bash
# Installation instructions here
```

<!-- Add a quick demo or screenshot -->

## What's Next

<!-- Share your roadmap — what features are coming? -->

## Try It Out

- GitHub: [{proj.name}]({proj.repo})
{"- Website: [" + proj.website + "](" + proj.website + ")" if proj.website else ""}

If you find it useful, I'd appreciate a {STAR} on GitHub!

**I'd love your feedback** {EM_DASH} what features would you like to see? Drop a comment below!

---

*{proj.name} is free and open-source. Contributions welcome!*
"""

    tips = """
---

## Dev.to Publishing Tips:
- Add a cover image (1000x420 recommended)
- Use 4 tags max (they must exist on Dev.to)
- Publish on Tuesday-Thursday for best engagement
- Cross-post to your personal blog if you have one
- Engage with every comment
- Share in Dev.to's #showdev tag
"""

    return {"devto_article.md": article + tips}
