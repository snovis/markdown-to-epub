"""
Command-line interface for markdown-to-epub.

Usage:
    md2epub note1.md note2.md -o book.epub
    md2epub *.md --vault ~/obsidian --title "My Book"
"""

from pathlib import Path

import click

from . import __version__
from .converter import convert_to_epub


@click.command()
@click.argument(
    "files",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-o", "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output EPUB file path. Defaults to first input file name with .epub extension.",
)
@click.option(
    "--vault",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Obsidian vault root directory (for resolving images and links).",
)
@click.option(
    "--title",
    help="Book title. Defaults to first note's title.",
)
@click.option(
    "--author",
    help="Book author. Defaults to first note's frontmatter author.",
)
@click.option(
    "--cover",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Cover image file.",
)
@click.option(
    "--wikilinks",
    type=click.Choice(["strip", "styled"]),
    default="strip",
    help="How to handle [[wikilinks]]: 'strip' removes syntax (default), 'styled' adds formatting.",
)
@click.option(
    "--no-highlight",
    is_flag=True,
    help="Disable syntax highlighting for code blocks.",
)
@click.option(
    "--code-style",
    default="default",
    help="Pygments style for code highlighting (default, monokai, github-dark, etc.).",
)
@click.option(
    "--no-toc",
    is_flag=True,
    help="Don't include table of contents.",
)
@click.option(
    "--no-optimize-images",
    is_flag=True,
    help="Don't resize/compress images.",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress progress output.",
)
@click.version_option(version=__version__)
def main(
    files: tuple[Path, ...],
    output: Path | None,
    vault: Path | None,
    title: str | None,
    author: str | None,
    cover: Path | None,
    wikilinks: str,
    no_highlight: bool,
    code_style: str,
    no_toc: bool,
    no_optimize_images: bool,
    quiet: bool,
) -> None:
    """
    Convert Obsidian markdown notes to EPUB.

    FILES are the markdown files to include, in chapter order.

    Examples:

        md2epub chapter1.md chapter2.md -o book.epub

        md2epub notes/*.md --vault ~/obsidian --title "My Notes"

        md2epub intro.md main.md conclusion.md --author "Jane Doe"
    """
    # Determine output path
    if output is None:
        output = files[0].with_suffix(".epub")

    # Progress callback
    def show_progress(current: int, total: int, message: str) -> None:
        if not quiet:
            click.echo(f"[{current}/{total}] {message}")

    try:
        result = convert_to_epub(
            files=list(files),
            output=output,
            vault_root=vault,
            title=title,
            author=author,
            cover=cover,
            wikilink_mode=wikilinks,
            highlight_code=not no_highlight,
            code_style=code_style,
            include_toc=not no_toc,
            optimize_images=not no_optimize_images,
            progress_callback=show_progress if not quiet else None,
        )

        if not quiet:
            click.echo(f"\nCreated: {result}")
            click.secho("Success!", fg="green")

    except FileNotFoundError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
