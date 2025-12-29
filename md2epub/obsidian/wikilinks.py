"""
Obsidian wikilink processing.

Converts Obsidian-style wikilinks:
    [[Note Name]]           -> plain text or link
    [[Note Name|Display]]   -> display text
    [[Note Name#Heading]]   -> with heading reference
"""

import re
from pathlib import Path


# Pattern to match wikilinks: [[target|display]] or [[target]]
# Excludes embeds which start with !
WIKILINK_PATTERN = re.compile(
    r"(?<!!)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"
)


def convert_wikilinks(
    content: str,
    mode: str = "strip",
    vault_root: Path | None = None,
    current_file: Path | None = None,
) -> str:
    """
    Convert Obsidian wikilinks to plain text or styled HTML.

    Modes:
        - "strip": Remove wikilink syntax, keep only display text (default)
                   [[ZUID-note-name|note-name]] -> note-name
        - "styled": Convert to styled span element
                    [[note]] -> <span class="wikilink">note</span>

    Args:
        content: Markdown content with potential wikilinks.
        mode: Conversion mode - "strip" or "styled".
        vault_root: Root path of the Obsidian vault.
        current_file: Path to the current file being processed.

    Returns:
        Content with wikilinks converted.
    """
    def replace_wikilink(match: re.Match) -> str:
        target = match.group(1).strip()
        display = match.group(2)

        # Handle heading references
        if "#" in target:
            target_parts = target.split("#", 1)
            note_name = target_parts[0].strip() or (
                current_file.stem if current_file else ""
            )
            heading = target_parts[1].strip()
            if display is None:
                display = heading if not note_name else f"{note_name} > {heading}"
        else:
            note_name = target
            heading = None
            if display is None:
                display = note_name

        # Strip mode: just return the display text (no HTML)
        if mode == "strip":
            return display

        # Styled mode: wrap in a span
        return f'<span class="wikilink">{display}</span>'

    return WIKILINK_PATTERN.sub(replace_wikilink, content)


def extract_wikilinks(content: str) -> list[str]:
    """
    Extract all wikilink targets from content.

    Useful for finding referenced notes that might need to be included.

    Args:
        content: Markdown content to scan.

    Returns:
        List of wikilink target note names (without display text or headings).
    """
    links = []
    for match in WIKILINK_PATTERN.finditer(content):
        target = match.group(1).strip()
        # Remove heading reference if present
        if "#" in target:
            target = target.split("#", 1)[0].strip()
        if target:  # Only add non-empty targets
            links.append(target)
    return links
