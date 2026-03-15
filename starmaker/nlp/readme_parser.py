"""README parser for extracting structured project information."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from starmaker.config import (
    ProjectConfig,
    PromotionConfig,
    StarMakerConfig,
)


@dataclass
class ReadmeContent:
    """Structured content extracted from a README file."""

    title: str = ""
    tagline: str = ""
    description: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    highlights: list[str] = field(default_factory=list)
    repo_url: str = ""
    tags: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    raw_text: str = ""


# Top ~100 English stopwords
STOPWORDS: frozenset[str] = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "can", "could", "did",
    "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "get", "got", "had", "has", "have", "having", "he", "her",
    "here", "hers", "herself", "him", "himself", "his", "how", "i", "if",
    "in", "into", "is", "it", "its", "itself", "just", "me", "might",
    "more", "most", "must", "my", "myself", "no", "nor", "not", "now", "of",
    "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves",
    "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "will", "with", "would",
    "you", "your", "yours", "yourself", "yourselves",
})

# Known tech/topic terms for tag inference
KNOWN_TAGS: list[str] = [
    "rust", "python", "javascript", "typescript", "react", "tauri",
    "linux", "macos", "windows", "docker", "cli", "api", "web",
    "desktop", "mobile", "privacy", "open-source",
]

# Tag -> default subreddit mapping
TAG_SUBREDDIT_MAP: dict[str, str] = {
    "rust": "rust",
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "react": "reactjs",
    "linux": "linux",
    "macos": "macos",
    "windows": "windows",
    "docker": "docker",
    "cli": "commandline",
    "api": "programming",
    "web": "webdev",
    "desktop": "software",
    "mobile": "mobiledev",
    "privacy": "privacy",
    "open-source": "opensource",
    "tauri": "tauri",
}


def parse_readme(text: str) -> ReadmeContent:
    """Parse a README string into structured ReadmeContent."""
    if not text or not text.strip():
        return ReadmeContent(raw_text=text or "")

    content = ReadmeContent(raw_text=text)

    # Extract title from first # heading
    content.title = _extract_title(text)

    # Extract tagline (first bold-only line)
    content.tagline = _extract_tagline(text)

    # Extract description (first regular paragraph, skipping badges/headings/bold)
    content.description = _extract_description(text)

    # Extract sections
    content.sections = _extract_sections(text)

    # Extract highlights from features section
    content.highlights = _extract_highlights(content.sections)

    # Detect repo URL
    content.repo_url = _detect_repo_url(text)

    # Infer tags
    content.tags = _infer_tags(text)

    # Tech stack is a subset of tags that are languages/frameworks
    tech_terms = {"rust", "python", "javascript", "typescript", "react", "tauri", "docker"}
    content.tech_stack = [t for t in content.tags if t in tech_terms]

    return content


def _extract_title(text: str) -> str:
    """Extract the title from the first # heading."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            return stripped[2:].strip()
    return ""


def _extract_tagline(text: str) -> str:
    """Extract the tagline from the first bold-only line."""
    for line in text.splitlines():
        stripped = line.strip()
        # Match lines that are entirely bold text: **...**
        match = re.match(r"^\*\*(.+)\*\*$", stripped)
        if match:
            return match.group(1)
    return ""


def _extract_description(text: str) -> str:
    """Extract the first regular paragraph, skipping badges, headings, bold lines, and blanks."""
    clean_text = _filter_code_blocks(text)
    lines = clean_text.splitlines()

    # Track when we've passed the title area
    past_title = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Skip headings
        if stripped.startswith("#"):
            past_title = True
            continue

        # Skip badges
        if _is_badge_line(stripped):
            continue

        # Skip bold-only lines (taglines)
        if re.match(r"^\*\*(.+)\*\*$", stripped):
            continue

        # This is a regular paragraph
        if past_title:
            return stripped

    return ""


def _is_badge_line(line: str) -> bool:
    """Check if a line is a badge/image line."""
    stripped = line.strip()
    return (
        stripped.startswith("[![")
        or "img.shields.io" in stripped
        or (stripped.startswith("![") and "](" in stripped)
    )


def _filter_badges(lines: list[str]) -> list[str]:
    """Remove badge/image lines from a list of lines."""
    return [line for line in lines if not _is_badge_line(line)]


def _filter_code_blocks(text: str) -> str:
    """Remove fenced code blocks from text."""
    # Remove ```...``` blocks
    result = re.sub(r"```[^\n]*\n.*?```", "", text, flags=re.DOTALL)
    return result


def _extract_sections(text: str) -> dict[str, str]:
    """Parse ## Heading sections into a dict of heading -> content."""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    clean_text = _filter_code_blocks(text)

    for line in clean_text.splitlines():
        stripped = line.strip()
        match = re.match(r"^##\s+(.+)$", stripped)
        if match:
            # Save previous section
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1).strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    # Save last section
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _extract_highlights(sections: dict[str, str]) -> list[str]:
    """Extract bullet items from a features-like section."""
    feature_keys = ["Key Features", "Features", "Highlights", "Why"]
    target_content = ""

    for key in feature_keys:
        if key in sections:
            target_content = sections[key]
            break

    if not target_content:
        return []

    highlights: list[str] = []
    for line in target_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            # Strip bold markers: **text** -> text
            item = re.sub(r"\*\*(.+?)\*\*", r"\1", item)
            highlights.append(item)

    return highlights


def _score_sentences(text: str, project_name: str = "") -> list[tuple[float, str]]:
    """Score sentences by relevance.

    Scoring factors:
    - Position: earlier sentences score higher
    - Project name: sentences containing the project name get a boost
    - Length: medium-length sentences preferred (penalise very short)
    """
    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    scored: list[tuple[float, str]] = []
    total = len(sentences)

    for i, sentence in enumerate(sentences):
        score = 0.0

        # Position score: first sentence gets 1.0, last gets close to 0
        position_score = 1.0 - (i / max(total, 1))
        score += position_score * 3.0

        # Project name boost
        if project_name and project_name.lower() in sentence.lower():
            score += 2.0

        # Length scoring: penalise very short sentences
        if len(sentence) < 20:
            score *= 0.1
        elif 50 <= len(sentence) <= 200:
            score += 1.0

        scored.append((score, sentence))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def get_top_sentences(text: str, n: int = 3, project_name: str = "") -> list[str]:
    """Return the top N scored sentences from text."""
    scored = _score_sentences(text, project_name)
    return [sentence for _, sentence in scored[:n]]


def _extract_keywords(text: str, max_count: int = 10) -> list[str]:
    """Extract the most frequent non-stopword terms from text."""
    # Tokenize: split on non-alphanumeric characters
    tokens = re.findall(r"[a-zA-Z]{2,}", text.lower())

    # Filter stopwords and very short tokens
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    # Count and return top N
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(max_count)]


def _infer_tags(text: str) -> list[str]:
    """Detect technology/topic tags from content."""
    text_lower = text.lower()
    tags: list[str] = []

    for tag in KNOWN_TAGS:
        # Use word boundary matching for short tags to avoid false positives
        pattern = r"\b" + re.escape(tag) + r"\b"
        if re.search(pattern, text_lower):
            tags.append(tag)

    return tags


def _detect_repo_url(text: str) -> str:
    """Find a GitHub or GitLab repository URL in text."""
    # Match github.com/user/repo or gitlab.com/user/repo
    match = re.search(
        r"https?://(?:www\.)?(?:github|gitlab)\.com/[\w.-]+/[\w.-]+",
        text,
    )
    return match.group(0) if match else ""


def build_config_from_readme(readme_text: str, repo_url: str = "") -> StarMakerConfig:
    """Build a StarMakerConfig from parsed README content."""
    content = parse_readme(readme_text)

    # Use provided repo_url or detected one
    final_repo = repo_url or content.repo_url

    project = ProjectConfig(
        name=content.title,
        repo=final_repo,
        tagline=content.tagline,
        description=content.description,
        highlights=content.highlights,
        tags=content.tags,
        tech_stack=content.tech_stack,
    )

    # Build default subreddits based on tags
    subreddits = []
    for tag in content.tags:
        if tag in TAG_SUBREDDIT_MAP:
            subreddits.append(TAG_SUBREDDIT_MAP[tag])

    promotion = PromotionConfig(
        reddit={"subreddits": subreddits} if subreddits else {},
    )

    return StarMakerConfig(
        project=project,
        promotion=promotion,
    )
