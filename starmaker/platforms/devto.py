"""Dev.to article draft generator."""

from __future__ import annotations

from starmaker.config import StarMakerConfig


def generate(config: StarMakerConfig) -> dict[str, str]:
    """Generate a Dev.to article draft."""
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

{"## Tech Stack" + chr(10) + chr(10) + tech_md if tech_md else ""}

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

If you find it useful, I'd appreciate a \u2b50 on GitHub!

**I'd love your feedback** \u2014 what features would you like to see? Drop a comment below!

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
