"""
YAML frontmatter parsing for Obsidian notes.

Handles extraction and parsing of YAML frontmatter from markdown files,
commonly used in Obsidian for metadata like title, author, tags, and dates.
"""

import re
from dataclasses import dataclass, field
from typing import Any

import yaml


# Pattern to match YAML frontmatter at the start of a document
FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n?",
    re.DOTALL
)


@dataclass
class Frontmatter:
    """Parsed frontmatter data from an Obsidian note."""

    title: str | None = None
    author: str | None = None
    date: str | None = None
    tags: list[str] = field(default_factory=list)
    description: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the raw frontmatter data."""
        return self.raw.get(key, default)


def extract_frontmatter(content: str) -> tuple[str, str]:
    """
    Extract frontmatter YAML and remaining content from a markdown string.

    Args:
        content: The full markdown content including potential frontmatter.

    Returns:
        A tuple of (frontmatter_yaml, remaining_content).
        If no frontmatter is found, frontmatter_yaml will be an empty string.
    """
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        yaml_content = match.group(1)
        remaining = content[match.end():]
        return yaml_content, remaining
    return "", content


def parse_frontmatter(content: str) -> tuple[Frontmatter, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: The full markdown content including potential frontmatter.

    Returns:
        A tuple of (Frontmatter object, remaining content without frontmatter).
    """
    yaml_str, remaining = extract_frontmatter(content)

    if not yaml_str:
        return Frontmatter(), content

    try:
        data = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError:
        # If YAML parsing fails, return empty frontmatter
        return Frontmatter(), content

    # Normalize tags - can be a list or space-separated string
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split() if t.strip()]
    elif not isinstance(tags, list):
        tags = []
    else:
        # Flatten and clean tags
        tags = [str(t).strip() for t in tags if t]

    # Handle date - convert to string if it's a datetime
    date = data.get("date")
    if date is not None:
        date = str(date)

    frontmatter = Frontmatter(
        title=data.get("title"),
        author=data.get("author"),
        date=date,
        tags=tags,
        description=data.get("description"),
        raw=data,
    )

    return frontmatter, remaining
