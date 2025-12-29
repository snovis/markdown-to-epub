"""
PDF generation using WeasyPrint.

Builds PDF documents from parsed markdown notes with:
- Chapters from individual notes
- Table of contents
- Embedded images
- CSS styling for callouts and code
- Print-optimized layout
"""

from datetime import datetime
from pathlib import Path

from .parser import ParsedNote
from .assets import AssetManager


# CSS optimized for PDF/print output
PDF_CSS = """
@page {
    size: letter;
    margin: 1in;
    @bottom-center {
        content: counter(page);
        font-family: Georgia, serif;
        font-size: 10pt;
        color: #666;
    }
}

@page:first {
    @bottom-center {
        content: none;
    }
}

/* Base styles */
body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    page-break-after: avoid;
}

h1 {
    font-size: 24pt;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.3em;
}

h2 { font-size: 18pt; }
h3 { font-size: 14pt; }
h4 { font-size: 12pt; }

/* Chapter titles - force page break before */
.chapter h1:first-child {
    page-break-before: always;
}

.chapter:first-of-type h1:first-child {
    page-break-before: avoid;
}

/* Code blocks */
pre, code {
    font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
    font-size: 9pt;
}

code {
    background-color: #f6f8fa;
    padding: 0.15em 0.3em;
    border-radius: 3px;
}

pre {
    background-color: #f6f8fa;
    padding: 0.8em;
    overflow-x: auto;
    border-radius: 4px;
    border: 1px solid #e1e4e8;
    page-break-inside: avoid;
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
    font-size: 10pt;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #ddd;
    padding: 6px 10px;
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
    border-left: 3px solid #ddd;
    margin: 1em 0;
    padding: 0.5em 1em;
    color: #555;
    background-color: #f9f9f9;
    page-break-inside: avoid;
}

/* Links - show URL in print */
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
    page-break-inside: avoid;
}

/* Highlights */
mark {
    background-color: #fff3a3;
    padding: 0.1em 0.2em;
}

/* Lists */
ul, ol {
    margin: 1em 0;
    padding-left: 1.5em;
}

li {
    margin: 0.3em 0;
}

/* Horizontal rules */
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}

/* Title page */
.title-page {
    page-break-after: always;
    text-align: center;
    padding-top: 30%;
}

.title-page .title {
    font-size: 32pt;
    font-weight: bold;
    margin-bottom: 0.3em;
    border: none;
}

.title-page .subtitle {
    font-size: 16pt;
    font-style: italic;
    color: #555;
    margin-bottom: 2em;
}

.title-page .author {
    font-size: 18pt;
    margin-top: 1em;
}

/* Copyright page */
.copyright-page {
    page-break-after: always;
    padding-top: 60%;
    font-size: 10pt;
}

.copyright-page p {
    margin: 0.6em 0;
}

/* Table of contents */
.toc {
    page-break-after: always;
}

.toc h1 {
    border: none;
}

.toc ul {
    list-style: none;
    padding-left: 0;
}

.toc li {
    margin: 0.5em 0;
    padding-left: 1em;
}

.toc a {
    text-decoration: none;
    color: #1a1a1a;
}

.toc .chapter-num {
    display: inline-block;
    width: 3em;
    color: #666;
}
"""


class PdfBuilder:
    """Builds PDF documents from parsed notes."""

    def __init__(
        self,
        title: str = "Untitled",
        author: str = "Unknown",
        subtitle: str | None = None,
        publisher: str | None = None,
        copyright_year: str | None = None,
        copyright_holder: str | None = None,
    ):
        self._title = title
        self._author = author
        self._subtitle = subtitle
        self._publisher = publisher
        self._copyright_year = copyright_year or str(datetime.now().year)
        self._copyright_holder = copyright_holder or author

        self.chapters: list[tuple[str, str]] = []  # (title, html_content)
        self.asset_manager: AssetManager | None = None
        self._cover_path: Path | None = None

    def set_cover(self, image_path: Path) -> None:
        """Set the cover image path."""
        if image_path.exists():
            self._cover_path = image_path

    def add_chapter(self, note: ParsedNote, chapter_number: int) -> None:
        """Add a chapter from a parsed note."""
        html_content = note.content_html
        if self.asset_manager:
            html_content = self.asset_manager.update_html_paths(html_content)
        self.chapters.append((note.title, html_content))

    def add_assets(self, asset_manager: AssetManager) -> None:
        """Store asset manager for path resolution."""
        self.asset_manager = asset_manager

    def _build_html(self, include_toc: bool = True) -> str:
        """Build complete HTML document for PDF conversion."""
        parts = ['<!DOCTYPE html>', '<html>', '<head>',
                 '<meta charset="utf-8">',
                 f'<title>{self._title}</title>',
                 f'<style>{PDF_CSS}</style>',
                 '</head>', '<body>']

        # Cover page (if we have a cover image)
        if self._cover_path:
            parts.append(f'''
            <div class="cover-page" style="page-break-after: always; text-align: center; padding-top: 10%;">
                <img src="{self._cover_path}" style="max-width: 80%; max-height: 80%;" alt="Cover">
            </div>
            ''')

        # Title page
        subtitle_html = f'<p class="subtitle">{self._subtitle}</p>' if self._subtitle else ''
        parts.append(f'''
        <div class="title-page">
            <h1 class="title">{self._title}</h1>
            {subtitle_html}
            <p class="author">{self._author}</p>
        </div>
        ''')

        # Copyright page
        publisher_html = f'<p>Published by {self._publisher}</p>' if self._publisher else ''
        parts.append(f'''
        <div class="copyright-page">
            <p><strong>{self._title}</strong></p>
            <p>Copyright © {self._copyright_year} by {self._copyright_holder}</p>
            {publisher_html}
            <p style="margin-top: 1.5em;">All rights reserved. No part of this publication may be reproduced,
            distributed, or transmitted in any form or by any means, including photocopying, recording,
            or other electronic or mechanical methods, without the prior written permission of the publisher,
            except in the case of brief quotations embodied in critical reviews and certain other
            noncommercial uses permitted by copyright law.</p>
        </div>
        ''')

        # Table of contents
        if include_toc:
            parts.append('<div class="toc">')
            parts.append('<h1>Contents</h1>')
            parts.append('<ul>')
            for i, (title, _) in enumerate(self.chapters):
                chapter_num = f"Chapter {i}" if i > 0 else "Prologue"
                parts.append(f'<li><span class="chapter-num">{chapter_num}:</span> {title}</li>')
            parts.append('</ul>')
            parts.append('</div>')

        # Chapters
        for title, content in self.chapters:
            parts.append(f'<div class="chapter">')
            parts.append(content)
            parts.append('</div>')

        parts.append('</body></html>')
        return '\n'.join(parts)

    def build(self, output_path: Path, include_toc: bool = True) -> None:
        """Build and write the PDF file."""
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "weasyprint is required for PDF export. "
                "Install with: pip install 'markdown-to-epub[pdf]'"
            )

        html_content = self._build_html(include_toc)

        # Determine base URL for resolving relative paths (images)
        base_url = None
        if self.asset_manager and self.asset_manager.vault_root:
            base_url = str(self.asset_manager.vault_root)

        # Generate PDF
        html = HTML(string=html_content, base_url=base_url)
        html.write_pdf(str(output_path))


def build_pdf(
    notes: list[ParsedNote],
    output_path: Path,
    title: str | None = None,
    author: str | None = None,
    cover_path: Path | None = None,
    asset_manager: AssetManager | None = None,
    include_toc: bool = True,
    subtitle: str | None = None,
    publisher: str | None = None,
    copyright_year: str | None = None,
    copyright_holder: str | None = None,
) -> None:
    """
    Build a PDF from a list of parsed notes.

    Args:
        notes: List of parsed notes (in chapter order).
        output_path: Where to write the PDF file.
        title: Book title.
        author: Book author.
        cover_path: Optional cover image path.
        asset_manager: Optional asset manager with images.
        include_toc: Whether to include a table of contents.
        subtitle: Book subtitle.
        publisher: Publisher name.
        copyright_year: Copyright year.
        copyright_holder: Copyright holder name.
    """
    if not notes:
        raise ValueError("No notes provided")

    if title is None:
        title = notes[0].title
    if author is None:
        author = notes[0].frontmatter.author or "Unknown"

    builder = PdfBuilder(
        title=title,
        author=author,
        subtitle=subtitle,
        publisher=publisher,
        copyright_year=copyright_year,
        copyright_holder=copyright_holder,
    )

    if cover_path:
        builder.set_cover(cover_path)

    if asset_manager:
        builder.add_assets(asset_manager)

    for i, note in enumerate(notes, 1):
        builder.add_chapter(note, i)

    builder.build(output_path, include_toc=include_toc)
