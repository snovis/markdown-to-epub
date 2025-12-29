"""
Obsidian embed processing.

Converts Obsidian-style embeds:
    ![[image.png]]           -> <img> tag
    ![[image.png|100]]       -> <img> with width
    ![[image.png|100x200]]   -> <img> with dimensions
    ![[note]]                -> embedded note content (placeholder)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable


# Pattern to match embeds: ![[target|size]] or ![[target]]
EMBED_PATTERN = re.compile(
    r"!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"
)

# Common image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}


def convert_embeds(
    content: str,
    vault_root: Path | None = None,
    current_file: Path | None = None,
    image_handler: Callable[[str], str] | None = None,
) -> str:
    """
    Convert Obsidian embeds to HTML.

    Image embeds are converted to <img> tags. Note embeds are converted
    to placeholder text (full note embedding would require recursion).

    Args:
        content: Markdown content with potential embeds.
        vault_root: Root path of the Obsidian vault.
        current_file: Path to the current file being processed.
        image_handler: Optional callback(image_path) that returns the EPUB
                      resource path for the image.

    Returns:
        Content with embeds converted.
    """
    def replace_embed(match: re.Match) -> str:
        target = match.group(1).strip()
        size_spec = match.group(2)

        # Check if this is an image embed
        target_path = Path(target)
        if target_path.suffix.lower() in IMAGE_EXTENSIONS:
            return _create_image_tag(target, size_spec, vault_root, image_handler)
        else:
            # Note embed - create a styled placeholder
            return _create_note_embed_placeholder(target)

    return EMBED_PATTERN.sub(replace_embed, content)


def _create_image_tag(
    image_path: str,
    size_spec: str | None,
    vault_root: Path | None,
    image_handler: Callable[[str], str] | None,
) -> str:
    """Create an HTML img tag for an embedded image."""
    # Parse size specification
    style_parts = []
    alt_text = Path(image_path).stem

    if size_spec:
        if "x" in size_spec:
            # WxH format
            parts = size_spec.split("x", 1)
            try:
                width = int(parts[0])
                height = int(parts[1])
                style_parts.append(f"width: {width}px")
                style_parts.append(f"height: {height}px")
            except ValueError:
                pass
        else:
            # Single number = width
            try:
                width = int(size_spec)
                style_parts.append(f"width: {width}px")
            except ValueError:
                # Might be alt text
                alt_text = size_spec

    # Get the src path
    if image_handler:
        src = image_handler(image_path)
    else:
        # Default: use relative path, will be fixed up by asset handler
        src = image_path

    style_attr = f' style="{"; ".join(style_parts)}"' if style_parts else ""

    return f'<img src="{src}" alt="{alt_text}"{style_attr} />'


def _create_note_embed_placeholder(note_name: str) -> str:
    """Create a placeholder for embedded notes."""
    style = (
        "border: 1px dashed #ccc; "
        "padding: 8px 12px; "
        "margin: 8px 0; "
        "background-color: #f9f9f9; "
        "border-radius: 4px; "
        "font-style: italic; "
        "color: #666;"
    )
    return f'<div class="embed-placeholder" style="{style}">Embedded note: {note_name}</div>'


def extract_image_embeds(content: str) -> list[str]:
    """
    Extract all embedded image paths from content.

    Args:
        content: Markdown content to scan.

    Returns:
        List of image paths found in embeds.
    """
    images = []
    for match in EMBED_PATTERN.finditer(content):
        target = match.group(1).strip()
        if Path(target).suffix.lower() in IMAGE_EXTENSIONS:
            images.append(target)
    return images
