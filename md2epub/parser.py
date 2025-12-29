"""
Markdown parser with Obsidian extensions and code highlighting.

Processes markdown content with full Obsidian syntax support:
- YAML frontmatter
- Callouts with colors
- Wikilinks
- Image embeds
- Code blocks with syntax highlighting
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.util import ClassNotFound

from .obsidian import (
    parse_frontmatter,
    convert_callouts,
    convert_wikilinks,
    convert_embeds,
    Frontmatter,
)


@dataclass
class ParsedNote:
    """A parsed Obsidian note ready for EPUB conversion."""

    title: str
    content_html: str
    frontmatter: Frontmatter
    source_path: Path | None = None
    images: list[str] = field(default_factory=list)


@dataclass
class ParserConfig:
    """Configuration for the markdown parser."""

    # Wikilink handling
    wikilink_mode: str = "strip"  # "strip" or "styled"

    # Code highlighting
    highlight_code: bool = True
    code_style: str = "default"  # Pygments style name

    # Image handling
    vault_root: Path | None = None

    # What to use as chapter title
    title_source: str = "auto"  # "auto", "frontmatter", "heading", "filename"


# Pattern to match fenced code blocks
CODE_BLOCK_PATTERN = re.compile(
    r"```(\w*)\n(.*?)```",
    re.DOTALL
)


def parse_note(
    content: str,
    source_path: Path | None = None,
    config: ParserConfig | None = None,
) -> ParsedNote:
    """
    Parse an Obsidian markdown note into HTML.

    Args:
        content: Raw markdown content of the note.
        source_path: Path to the source file (for context).
        config: Parser configuration options.

    Returns:
        ParsedNote with HTML content and metadata.
    """
    if config is None:
        config = ParserConfig()

    # Step 1: Extract frontmatter
    frontmatter, markdown_content = parse_frontmatter(content)

    # Step 2: Process code blocks first (before other transformations)
    if config.highlight_code:
        markdown_content = _highlight_code_blocks(markdown_content, config.code_style)

    # Step 3: Convert Obsidian callouts
    markdown_content = convert_callouts(markdown_content)

    # Step 4: Extract image embeds for asset collection
    from .obsidian.embeds import extract_image_embeds
    images = extract_image_embeds(markdown_content)

    # Step 5: Convert embeds to HTML
    markdown_content = convert_embeds(
        markdown_content,
        vault_root=config.vault_root,
        current_file=source_path,
    )

    # Step 6: Convert wikilinks
    markdown_content = convert_wikilinks(
        markdown_content,
        mode=config.wikilink_mode,
        vault_root=config.vault_root,
        current_file=source_path,
    )

    # Step 7: Convert remaining markdown to HTML
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "footnotes",
            "toc",
            "nl2br",
        ]
    )
    html_content = md.convert(markdown_content)

    # Step 8: Determine title
    title = _determine_title(
        frontmatter,
        markdown_content,
        source_path,
        config.title_source,
    )

    return ParsedNote(
        title=title,
        content_html=html_content,
        frontmatter=frontmatter,
        source_path=source_path,
        images=images,
    )


def _highlight_code_blocks(content: str, style: str = "default") -> str:
    """
    Apply syntax highlighting to fenced code blocks.

    Replaces ```lang ... ``` blocks with highlighted HTML.
    Uses inline CSS for EPUB compatibility.
    """
    formatter = HtmlFormatter(
        style=style,
        noclasses=True,  # Inline styles for EPUB
        nowrap=False,
        linenos=False,
    )

    def replace_code_block(match: re.Match) -> str:
        lang = match.group(1).strip().lower()
        code = match.group(2)

        # Get the appropriate lexer
        try:
            if lang:
                lexer = get_lexer_by_name(lang)
            else:
                # Try to guess the language
                try:
                    lexer = guess_lexer(code)
                except ClassNotFound:
                    lexer = TextLexer()
        except ClassNotFound:
            lexer = TextLexer()

        # Generate highlighted HTML
        highlighted = highlight(code, lexer, formatter)

        # Wrap in a container for styling
        return f'<div class="code-block">{highlighted}</div>'

    return CODE_BLOCK_PATTERN.sub(replace_code_block, content)


def _determine_title(
    frontmatter: Frontmatter,
    content: str,
    source_path: Path | None,
    source: str,
) -> str:
    """Determine the chapter title from available sources."""

    # For Obsidian notes, check aliases[0] first (common pattern)
    if source in ("frontmatter", "auto"):
        aliases = frontmatter.get("aliases") or frontmatter.get("Aliases")
        if aliases and len(aliases) > 0:
            return aliases[0]

    # Check frontmatter title
    if source in ("frontmatter", "auto") and frontmatter.title:
        return frontmatter.title

    # Try first heading
    if source in ("heading", "auto"):
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

    # Fall back to filename
    if source_path:
        return source_path.stem.replace("-", " ").replace("_", " ").title()

    return "Untitled"


def get_code_highlight_css(style: str = "default") -> str:
    """
    Get CSS for code highlighting.

    For EPUB, styles are inlined, but this can be used for
    additional styling or debugging.
    """
    formatter = HtmlFormatter(style=style)
    return formatter.get_style_defs(".highlight")
