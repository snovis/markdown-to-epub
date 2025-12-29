# CLAUDE.md - Project Context for Claude Code

## Project: md2epub
Convert Obsidian markdown notes to EPUB format for reading on iBooks and reMarkable.

## Quick Start
```bash
source .venv/bin/activate
pip install -e ".[dev]"
md2epub note1.md note2.md --output book.epub
```

## Key Features
- **Input**: Individual markdown files specified on command line (order preserved = chapter order)
- **Output**: Single combined EPUB with each note as a chapter
- **Obsidian Features**: Full support for callouts, wikilinks, embeds, frontmatter, tags
- **Code Blocks**: Syntax highlighting with Pygments
- **Callouts**: Color-coded styling matching Obsidian defaults (blue note, green tip, orange warning, red danger, etc.)
- **Images**: Embedded from vault
- **Wikilinks**: Strip mode (default) removes `[[link|text]]` syntax, shows only display text

## Architecture
```
md2epub/
├── __init__.py           # Package init, exports convert_to_epub
├── cli.py                # Click CLI entry point (md2epub command)
├── converter.py          # Main orchestration
├── parser.py             # Markdown parsing with Obsidian extensions
├── epub_builder.py       # EPUB generation using ebooklib
├── assets.py             # Image/asset handling
└── obsidian/
    ├── __init__.py
    ├── frontmatter.py    # YAML frontmatter extraction
    ├── callouts.py       # Callout conversion with colors
    ├── wikilinks.py      # [[wikilink]] processing (strip or styled)
    └── embeds.py         # ![[embed]] processing
```

## CLI Options
```bash
md2epub FILE1.md FILE2.md ... [OPTIONS]

Options:
  -o, --output FILE           Output EPUB file path
  --vault DIRECTORY           Obsidian vault root (for images)
  --title TEXT                Override EPUB title
  --author TEXT               Override author
  --cover FILE                Cover image
  --wikilinks [strip|styled]  Wikilink handling (default: strip)
  --no-highlight              Disable code syntax highlighting
  --code-style TEXT           Pygments style (default, monokai, etc.)
  --no-toc                    Don't include table of contents
  --no-optimize-images        Don't resize/compress images
  -q, --quiet                 Suppress progress output
```

## Key Libraries
- ebooklib: EPUB generation
- markdown: Base markdown parsing
- click: CLI interface
- pyyaml: Frontmatter parsing
- Pillow: Image processing
- Pygments: Syntax highlighting

## Callout Colors (Reference)
| Type | Color | Background |
|------|-------|------------|
| note/info | #448aff | #e3f2fd |
| tip/hint | #00c853 | #e8f5e9 |
| warning/caution | #ff9100 | #fff3e0 |
| danger/error | #ff5252 | #ffebee |
| example | #7c4dff | #ede7f6 |
| quote | #9e9e9e | #f5f5f5 |

## Development
```bash
# Activate venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Test conversion
md2epub tests/sample_note.md -o tests/output.epub

# Build package
pip install build
python -m build
```
