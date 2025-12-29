# /obsidian-to-epub

Convert Obsidian markdown notes to EPUB format.

## Usage

When the user wants to convert markdown notes to EPUB, help them by:

1. **Collecting the files**: Ask which markdown files they want to include
2. **Determining order**: Files are added as chapters in the order specified
3. **Running the conversion**: Use the `md2epub` command

## Command Examples

```bash
# Basic conversion - single file
source .venv/bin/activate && md2epub note.md -o book.epub

# Multiple files as chapters (order matters)
source .venv/bin/activate && md2epub intro.md chapter1.md chapter2.md conclusion.md -o book.epub

# With vault root for images
source .venv/bin/activate && md2epub notes/*.md --vault ~/obsidian --output book.epub

# Custom title and author
source .venv/bin/activate && md2epub *.md --title "My Book" --author "Jane Doe" -o book.epub

# With cover image
source .venv/bin/activate && md2epub notes/*.md --cover cover.png -o book.epub
```

## Options Reference

| Option | Description |
|--------|-------------|
| `-o, --output` | Output EPUB file path |
| `--vault` | Obsidian vault root for resolving images |
| `--title` | Override EPUB title |
| `--author` | Override author |
| `--cover` | Cover image file |
| `--wikilinks strip\|styled` | How to handle wikilinks (default: strip) |
| `--no-highlight` | Disable syntax highlighting |
| `--code-style` | Pygments style (default, monokai, etc.) |
| `--no-toc` | Skip table of contents |
| `-q, --quiet` | Suppress progress output |

## Supported Features

- YAML frontmatter (title, author, tags, date)
- Obsidian callouts with colors (note, tip, warning, danger, example, quote)
- Wikilinks (`[[link|display]]` - stripped to display text by default)
- Image embeds (`![[image.png]]`)
- Code blocks with syntax highlighting
- Tables, footnotes, blockquotes

## Workflow

1. User provides list of markdown files
2. Each file becomes a chapter (order preserved)
3. Chapter titles from: frontmatter `title` > first `# heading` > filename
4. Images are collected and embedded in EPUB
5. Output EPUB ready for iBooks or reMarkable
