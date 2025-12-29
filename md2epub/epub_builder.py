"""
EPUB generation using ebooklib.

Builds EPUB documents from parsed markdown notes with:
- Chapters from individual notes
- Table of contents
- Embedded images
- CSS styling for callouts and code
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from ebooklib import epub

from .parser import ParsedNote
from .assets import AssetManager


# Default CSS for the EPUB
DEFAULT_CSS = """
/* Base styles */
body {
    font-family: Georgia, serif;
    line-height: 1.6;
    margin: 1em;
    color: #333;
}

h1, h2, h3, h4, h5, h6 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 { font-size: 1.8em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; }
h3 { font-size: 1.3em; }

/* Code blocks */
pre, code {
    font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
    font-size: 0.9em;
}

code {
    background-color: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
}

pre {
    background-color: #f6f8fa;
    padding: 1em;
    overflow-x: auto;
    border-radius: 6px;
    border: 1px solid #e1e4e8;
}

pre code {
    background: none;
    padding: 0;
}

.code-block {
    margin: 1em 0;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #f6f8fa;
    font-weight: bold;
}

tr:nth-child(even) {
    background-color: #fafbfc;
}

/* Blockquotes */
blockquote {
    border-left: 4px solid #ddd;
    margin: 1em 0;
    padding: 0.5em 1em;
    color: #666;
    background-color: #f9f9f9;
}

/* Links */
a {
    color: #0366d6;
    text-decoration: none;
}

/* Wikilinks */
.wikilink {
    color: #0366d6;
    font-style: italic;
}

/* Images */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

/* Footnotes */
.footnote {
    font-size: 0.85em;
}

/* Lists */
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

li {
    margin: 0.5em 0;
}

/* Horizontal rules */
hr {
    border: none;
    border-top: 1px solid #eee;
    margin: 2em 0;
}
"""


class EpubBuilder:
    """Builds EPUB documents from parsed notes."""

    def __init__(
        self,
        title: str = "Untitled",
        author: str = "Unknown",
        language: str = "en",
    ):
        """
        Initialize the EPUB builder.

        Args:
            title: Book title.
            author: Book author.
            language: Book language code.
        """
        self.book = epub.EpubBook()
        self.chapters: list[epub.EpubHtml] = []
        self.asset_manager: AssetManager | None = None

        # Set metadata
        self.book.set_identifier(f"md2epub-{uuid4().hex[:8]}")
        self.book.set_title(title)
        self.book.set_language(language)
        self.book.add_author(author)
        self.book.add_metadata("DC", "date", datetime.now().isoformat())

        # Add default CSS
        self._add_default_css()

    def _add_default_css(self) -> None:
        """Add the default stylesheet."""
        css = epub.EpubItem(
            uid="style_default",
            file_name="style/default.css",
            media_type="text/css",
            content=DEFAULT_CSS.encode("utf-8"),
        )
        self.book.add_item(css)
        self._default_css = css

    def set_cover(self, image_path: Path) -> None:
        """
        Set the book cover image.

        Args:
            image_path: Path to the cover image file.
        """
        if not image_path.exists():
            return

        content = image_path.read_bytes()
        self.book.set_cover(image_path.name, content)

    def add_chapter(
        self,
        note: ParsedNote,
        chapter_number: int,
    ) -> epub.EpubHtml:
        """
        Add a chapter from a parsed note.

        Args:
            note: The parsed note to add.
            chapter_number: Chapter number for ordering.

        Returns:
            The created EpubHtml chapter.
        """
        # Create chapter
        chapter_id = f"chapter_{chapter_number:03d}"
        filename = f"{chapter_id}.xhtml"

        # Update image paths if we have an asset manager
        html_content = note.content_html
        if self.asset_manager:
            html_content = self.asset_manager.update_html_paths(html_content)

        # Create full HTML document
        full_html = self._wrap_chapter_html(note.title, html_content)

        chapter = epub.EpubHtml(
            title=note.title,
            file_name=filename,
            lang=self.book.language,
        )
        chapter.set_content(full_html)
        chapter.add_item(self._default_css)

        self.book.add_item(chapter)
        self.chapters.append(chapter)

        return chapter

    def _wrap_chapter_html(self, title: str, content: str) -> str:
        """Wrap chapter content in a full HTML document."""
        # Note: ebooklib handles XML declaration and doctype internally
        return f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
    <h1>{title}</h1>
    {content}
</body>
</html>"""

    def add_assets(self, asset_manager: AssetManager) -> None:
        """
        Add all assets from an AssetManager to the EPUB.

        Args:
            asset_manager: The asset manager with collected images.
        """
        self.asset_manager = asset_manager

        for path, data in asset_manager.get_assets().items():
            mime_type = asset_manager.get_mime_type(path)
            item = epub.EpubItem(
                file_name=path,
                media_type=mime_type,
                content=data,
            )
            self.book.add_item(item)

    def build(self, output_path: Path, include_toc: bool = True) -> None:
        """
        Build and write the EPUB file.

        Args:
            output_path: Where to write the EPUB file.
            include_toc: Whether to include a table of contents.
        """
        # Define spine (reading order)
        spine_items = ["nav"] if include_toc else []
        spine_items.extend(self.chapters)
        self.book.spine = spine_items

        # Define TOC
        if include_toc:
            self.book.toc = self.chapters
            self.book.add_item(epub.EpubNcx())
            self.book.add_item(epub.EpubNav())

        # Write the file
        epub.write_epub(str(output_path), self.book, {})


def build_epub(
    notes: list[ParsedNote],
    output_path: Path,
    title: str | None = None,
    author: str | None = None,
    cover_path: Path | None = None,
    asset_manager: AssetManager | None = None,
    include_toc: bool = True,
) -> None:
    """
    Build an EPUB from a list of parsed notes.

    Convenience function that handles the full build process.

    Args:
        notes: List of parsed notes (in chapter order).
        output_path: Where to write the EPUB file.
        title: Book title (defaults to first note's title).
        author: Book author (defaults to first note's frontmatter author).
        cover_path: Optional cover image path.
        asset_manager: Optional asset manager with images.
        include_toc: Whether to include a table of contents.
    """
    if not notes:
        raise ValueError("No notes provided")

    # Determine title and author
    if title is None:
        title = notes[0].title
    if author is None:
        author = notes[0].frontmatter.author or "Unknown"

    # Create builder
    builder = EpubBuilder(title=title, author=author)

    # Add cover if provided
    if cover_path:
        builder.set_cover(cover_path)

    # Add assets
    if asset_manager:
        builder.add_assets(asset_manager)

    # Add chapters
    for i, note in enumerate(notes, 1):
        builder.add_chapter(note, i)

    # Build and write
    builder.build(output_path, include_toc=include_toc)
