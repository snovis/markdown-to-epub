#!/usr/bin/env python3
"""
Build an EPUB from Obsidian notes with specific tag and chapter ordering.

Usage:
    python scripts/build_ebook.py /path/to/vault/folder --output book.epub
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}
    return {}


def has_tag(frontmatter: dict, tag: str) -> bool:
    """Check if frontmatter has a specific tag (case-insensitive)."""
    tags = frontmatter.get("tags") or frontmatter.get("Tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    return any(t.lower() == tag.lower() for t in tags)


def get_chapter_number(frontmatter: dict) -> int:
    """Get the Chapter number from frontmatter."""
    # Can't use `or` here because Chapter: 0 would be falsy
    chapter = frontmatter.get("Chapter")
    if chapter is None:
        chapter = frontmatter.get("chapter")
    if chapter is not None:
        try:
            return int(chapter)
        except (ValueError, TypeError):
            return 999
    return 999


def get_chapter_title(frontmatter: dict, content: str) -> str:
    """Get chapter title from aliases[0] or first heading."""
    # Try aliases first
    aliases = frontmatter.get("aliases") or frontmatter.get("Aliases") or []
    if aliases and len(aliases) > 0:
        return aliases[0]

    # Fall back to first H1 heading
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    return "Untitled"


def find_ebook_files(folder: Path, tag: str = "4epub") -> list[tuple[Path, int, str]]:
    """
    Find all markdown files with the specified tag.

    Returns list of (path, chapter_number, title) tuples sorted by chapter.
    """
    files = []

    for md_file in folder.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)

        if has_tag(frontmatter, tag):
            chapter_num = get_chapter_number(frontmatter)
            title = get_chapter_title(frontmatter, content)
            files.append((md_file, chapter_num, title))

    # Sort by chapter number
    files.sort(key=lambda x: x[1])
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Build EPUB from Obsidian notes with 4epub tag"
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing markdown files"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output EPUB file"
    )
    parser.add_argument(
        "--tag",
        default="4epub",
        help="Tag to filter files (default: 4epub)"
    )
    parser.add_argument(
        "--title",
        help="Book title"
    )
    parser.add_argument(
        "--author",
        help="Book author"
    )
    parser.add_argument(
        "--cover",
        type=Path,
        help="Cover image file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Just show what would be included"
    )

    args = parser.parse_args()

    if not args.folder.exists():
        print(f"Error: Folder not found: {args.folder}", file=sys.stderr)
        sys.exit(1)

    # Find files
    files = find_ebook_files(args.folder, args.tag)

    if not files:
        print(f"No files found with tag '{args.tag}'", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} chapters:\n")
    for path, chapter_num, title in files:
        print(f"  Chapter {chapter_num}: {title}")
        print(f"    File: {path.name}")

    if args.dry_run:
        return

    # Build the md2epub command
    file_paths = [str(f[0]) for f in files]
    output = args.output or args.folder / "ebook.epub"

    # Get author from first file if not specified
    if not args.author:
        content = files[0][0].read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        args.author = fm.get("Author") or fm.get("author") or "Unknown"

    # Get title if not specified
    if not args.title:
        # Use folder name or first meaningful part
        args.title = args.folder.name.replace("eBook", "").strip()

    print(f"\nBuilding EPUB: {output}")
    print(f"Title: {args.title}")
    print(f"Author: {args.author}")
    if args.cover:
        print(f"Cover: {args.cover}")

    # Import and run the converter
    from md2epub.converter import convert_to_epub

    def progress(current, total, message):
        print(f"  [{current}/{total}] {message}")

    convert_to_epub(
        files=[f[0] for f in files],
        output=output,
        vault_root=args.folder.parent,
        title=args.title,
        author=args.author,
        cover=args.cover,
        progress_callback=progress,
    )

    print(f"\nSuccess! Created: {output}")


if __name__ == "__main__":
    main()
