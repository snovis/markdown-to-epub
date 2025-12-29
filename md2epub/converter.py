"""
Main conversion orchestration.

Coordinates the full conversion pipeline from markdown files to EPUB or PDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .assets import AssetManager
from .epub_builder import build_epub
from .parser import parse_note, ParserConfig, ParsedNote


def convert_to_epub(
    files: list[Path],
    output: Path,
    vault_root: Path | None = None,
    title: str | None = None,
    author: str | None = None,
    cover: Path | None = None,
    wikilink_mode: str = "strip",
    highlight_code: bool = True,
    code_style: str = "default",
    include_toc: bool = True,
    optimize_images: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
    subtitle: str | None = None,
    publisher: str | None = None,
    copyright_year: str | None = None,
    copyright_holder: str | None = None,
) -> Path:
    """
    Convert markdown files to an EPUB.

    Args:
        files: List of markdown file paths (in chapter order).
        output: Output EPUB file path.
        vault_root: Obsidian vault root for resolving images.
        title: Book title (defaults to first note's title).
        author: Book author (defaults to first note's author).
        cover: Optional cover image path.
        wikilink_mode: How to handle wikilinks ("strip" or "styled").
        highlight_code: Whether to syntax-highlight code blocks.
        code_style: Pygments style for code highlighting.
        include_toc: Whether to include table of contents.
        optimize_images: Whether to resize/compress images.
        progress_callback: Optional callback(current, total, message).
        subtitle: Book subtitle for title page.
        publisher: Publisher name for copyright page.
        copyright_year: Copyright year.
        copyright_holder: Copyright holder name.

    Returns:
        Path to the created EPUB file.
    """
    if not files:
        raise ValueError("No input files provided")

    def report_progress(current: int, total: int, message: str) -> None:
        if progress_callback:
            progress_callback(current, total, message)

    # Setup
    total_steps = len(files) + 2  # files + asset collection + build
    asset_manager = AssetManager(vault_root=vault_root)

    # Parser configuration
    config = ParserConfig(
        wikilink_mode=wikilink_mode,
        highlight_code=highlight_code,
        code_style=code_style,
        vault_root=vault_root,
    )

    # Parse all notes
    notes: list[ParsedNote] = []
    for i, file_path in enumerate(files, 1):
        report_progress(i, total_steps, f"Parsing {file_path.name}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        note = parse_note(content, source_path=file_path, config=config)
        notes.append(note)

        # Collect images from this note
        for image_ref in note.images:
            asset_manager.add_image(
                image_ref,
                source_file=file_path,
                optimize=optimize_images,
            )

    # Build EPUB
    report_progress(len(files) + 1, total_steps, "Building EPUB")

    build_epub(
        notes=notes,
        output_path=output,
        title=title,
        author=author,
        cover_path=cover,
        asset_manager=asset_manager,
        include_toc=include_toc,
        subtitle=subtitle,
        publisher=publisher,
        copyright_year=copyright_year,
        copyright_holder=copyright_holder,
    )

    report_progress(total_steps, total_steps, "Done")

    return output


def convert_to_pdf(
    files: list[Path],
    output: Path,
    vault_root: Path | None = None,
    title: str | None = None,
    author: str | None = None,
    cover: Path | None = None,
    wikilink_mode: str = "strip",
    highlight_code: bool = True,
    code_style: str = "default",
    include_toc: bool = True,
    optimize_images: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
    subtitle: str | None = None,
    publisher: str | None = None,
    copyright_year: str | None = None,
    copyright_holder: str | None = None,
) -> Path:
    """
    Convert markdown files to a PDF.

    Args:
        files: List of markdown file paths (in chapter order).
        output: Output PDF file path.
        vault_root: Obsidian vault root for resolving images.
        title: Book title (defaults to first note's title).
        author: Book author (defaults to first note's author).
        cover: Optional cover image path.
        wikilink_mode: How to handle wikilinks ("strip" or "styled").
        highlight_code: Whether to syntax-highlight code blocks.
        code_style: Pygments style for code highlighting.
        include_toc: Whether to include table of contents.
        optimize_images: Whether to resize/compress images.
        progress_callback: Optional callback(current, total, message).
        subtitle: Book subtitle for title page.
        publisher: Publisher name for copyright page.
        copyright_year: Copyright year.
        copyright_holder: Copyright holder name.

    Returns:
        Path to the created PDF file.
    """
    from .pdf_builder import build_pdf

    if not files:
        raise ValueError("No input files provided")

    def report_progress(current: int, total: int, message: str) -> None:
        if progress_callback:
            progress_callback(current, total, message)

    # Setup
    total_steps = len(files) + 2  # files + asset collection + build
    asset_manager = AssetManager(vault_root=vault_root)

    # Parser configuration
    config = ParserConfig(
        wikilink_mode=wikilink_mode,
        highlight_code=highlight_code,
        code_style=code_style,
        vault_root=vault_root,
    )

    # Parse all notes
    notes: list[ParsedNote] = []
    for i, file_path in enumerate(files, 1):
        report_progress(i, total_steps, f"Parsing {file_path.name}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        note = parse_note(content, source_path=file_path, config=config)
        notes.append(note)

        # Collect images from this note
        for image_ref in note.images:
            asset_manager.add_image(
                image_ref,
                source_file=file_path,
                optimize=optimize_images,
            )

    # Build PDF
    report_progress(len(files) + 1, total_steps, "Building PDF")

    build_pdf(
        notes=notes,
        output_path=output,
        title=title,
        author=author,
        cover_path=cover,
        asset_manager=asset_manager,
        include_toc=include_toc,
        subtitle=subtitle,
        publisher=publisher,
        copyright_year=copyright_year,
        copyright_holder=copyright_holder,
    )

    report_progress(total_steps, total_steps, "Done")

    return output
