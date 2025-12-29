# make-ebook

Guide the user through creating an EPUB and/or PDF book from Obsidian notes.

## Triggers
- "let's make an ebook"
- "create an ebook"
- "build an ebook"
- "make a book"
- "convert notes to epub"
- "convert notes to pdf"

## Workflow

### Step 1: Gather Information

Ask the user for the following (use AskUserQuestion tool):

1. **Folder path**: Where are the Obsidian notes located?
2. **Output format**: EPUB, PDF, or both?

### Step 2: Scan the Folder

Run a dry-run to show what will be included:

```bash
source .venv/bin/activate && python scripts/build_ebook.py "/path/to/folder" --dry-run
```

Show the user the chapters found and confirm they look correct.

### Step 3: Gather Book Metadata

Ask for any metadata not already known:

- **Title**: Book title
- **Subtitle**: Optional subtitle for title page
- **Cover image**: Path to cover image (look for .png/.jpg files in the folder)
- **Publisher**: Publisher name for copyright page
- **Copyright year**: Default to current year
- **Copyright holder**: Who holds the copyright

### Step 4: Build the Book

Run the build command:

```bash
source .venv/bin/activate && python scripts/build_ebook.py "/path/to/folder" \
  --title "Book Title" \
  --subtitle "Subtitle" \
  --cover "/path/to/cover.png" \
  --publisher "Publisher Name" \
  --copyright-year "2025" \
  --copyright-holder "Copyright Holder"
```

Add `--pdf` flag if PDF was requested. Run twice (once without, once with `--pdf`) if both formats requested.

### Step 5: Open for Review

Open the generated file(s) for the user to review:

```bash
open "/path/to/folder/ebook.epub"
open "/path/to/folder/ebook.pdf"
```

## Requirements for Source Notes

Remind the user their Obsidian notes need:

- `4epub` tag in YAML frontmatter (or custom tag with `--tag` option)
- `Chapter: N` property for ordering (0 = prologue, 1+ = chapters)
- `aliases: ["Chapter Title"]` for chapter names (or H1 heading as fallback)

## Example Frontmatter

```yaml
---
aliases:
  - My Chapter Title
Author: Author Name
Chapter: 1
tags:
  - 4epub
---
```
