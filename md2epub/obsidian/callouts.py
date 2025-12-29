"""
Obsidian callout block conversion.

Converts Obsidian-style callouts like:
    > [!note]
    > This is a note

Into styled HTML blocks with appropriate colors.
"""

import re
from dataclasses import dataclass


@dataclass
class CalloutStyle:
    """Styling information for a callout type."""

    color: str  # Primary color (border/accent)
    background: str  # Background color (lighter version)
    label: str  # Display label


# Obsidian callout types with their colors (matching Obsidian's defaults)
CALLOUT_STYLES: dict[str, CalloutStyle] = {
    # Note/Info types - Blue
    "note": CalloutStyle("#448aff", "#e3f2fd", "Note"),
    "info": CalloutStyle("#448aff", "#e3f2fd", "Info"),
    "abstract": CalloutStyle("#448aff", "#e3f2fd", "Abstract"),
    "summary": CalloutStyle("#448aff", "#e3f2fd", "Summary"),
    "tldr": CalloutStyle("#448aff", "#e3f2fd", "TL;DR"),

    # Tip/Hint types - Green
    "tip": CalloutStyle("#00c853", "#e8f5e9", "Tip"),
    "hint": CalloutStyle("#00c853", "#e8f5e9", "Hint"),
    "important": CalloutStyle("#00c853", "#e8f5e9", "Important"),

    # Success/Check types - Green
    "success": CalloutStyle("#00c853", "#e8f5e9", "Success"),
    "check": CalloutStyle("#00c853", "#e8f5e9", "Check"),
    "done": CalloutStyle("#00c853", "#e8f5e9", "Done"),

    # Question/Help types - Yellow
    "question": CalloutStyle("#ffb300", "#fff8e1", "Question"),
    "help": CalloutStyle("#ffb300", "#fff8e1", "Help"),
    "faq": CalloutStyle("#ffb300", "#fff8e1", "FAQ"),

    # Warning/Caution types - Orange
    "warning": CalloutStyle("#ff9100", "#fff3e0", "Warning"),
    "caution": CalloutStyle("#ff9100", "#fff3e0", "Caution"),
    "attention": CalloutStyle("#ff9100", "#fff3e0", "Attention"),

    # Danger/Error types - Red
    "danger": CalloutStyle("#ff5252", "#ffebee", "Danger"),
    "error": CalloutStyle("#ff5252", "#ffebee", "Error"),
    "failure": CalloutStyle("#ff5252", "#ffebee", "Failure"),
    "fail": CalloutStyle("#ff5252", "#ffebee", "Fail"),
    "missing": CalloutStyle("#ff5252", "#ffebee", "Missing"),

    # Bug type - Red
    "bug": CalloutStyle("#ff5252", "#ffebee", "Bug"),

    # Example type - Purple
    "example": CalloutStyle("#7c4dff", "#ede7f6", "Example"),

    # Quote/Cite types - Gray
    "quote": CalloutStyle("#9e9e9e", "#f5f5f5", "Quote"),
    "cite": CalloutStyle("#9e9e9e", "#f5f5f5", "Cite"),
}

# Default style for unknown callout types
DEFAULT_STYLE = CalloutStyle("#9e9e9e", "#f5f5f5", "Note")

# Pattern to match callout start: > [!type] optional title
# Supports folding indicators (+/-) which we ignore for EPUB
CALLOUT_START_PATTERN = re.compile(
    r"^>\s*\[!(\w+)\]([+-])?\s*(.*)?$",
    re.MULTILINE
)


def get_callout_style(callout_type: str) -> CalloutStyle:
    """Get the style for a callout type, with fallback to default."""
    return CALLOUT_STYLES.get(callout_type.lower(), DEFAULT_STYLE)


def convert_callouts(content: str) -> str:
    """
    Convert Obsidian callouts to styled HTML divs.

    Args:
        content: Markdown content with potential callouts.

    Returns:
        Content with callouts converted to styled HTML.
    """
    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        match = CALLOUT_START_PATTERN.match(line)

        if match:
            callout_type = match.group(1)
            custom_title = match.group(3)
            style = get_callout_style(callout_type)

            # Use custom title if provided, otherwise use default label
            title = custom_title.strip() if custom_title and custom_title.strip() else style.label

            # Collect callout content (subsequent lines starting with >)
            callout_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.startswith(">"):
                    # Remove the > prefix and optional space
                    content_line = next_line[1:]
                    if content_line.startswith(" "):
                        content_line = content_line[1:]
                    callout_lines.append(content_line)
                    i += 1
                elif next_line.strip() == "":
                    # Empty line might continue the callout if next line has >
                    if i + 1 < len(lines) and lines[i + 1].startswith(">"):
                        callout_lines.append("")
                        i += 1
                    else:
                        break
                else:
                    break

            # Build the styled HTML
            callout_content = "\n".join(callout_lines)
            html = _build_callout_html(callout_type, title, callout_content, style)
            result.append(html)
        else:
            result.append(line)
            i += 1

    return "\n".join(result)


def _build_callout_html(
    callout_type: str,
    title: str,
    content: str,
    style: CalloutStyle,
) -> str:
    """Build the HTML for a callout block."""
    # Inline styles for EPUB compatibility (no external CSS)
    container_style = (
        f"border-left: 4px solid {style.color}; "
        f"background-color: {style.background}; "
        "padding: 12px 16px; "
        "margin: 16px 0; "
        "border-radius: 4px;"
    )

    title_style = (
        f"color: {style.color}; "
        "font-weight: bold; "
        "margin: 0 0 8px 0; "
        "font-size: 1em;"
    )

    content_style = "margin: 0; line-height: 1.6;"

    # Escape content for HTML (basic escaping, markdown will be processed later)
    # Don't escape here since this will be passed through markdown processor

    return f"""<div class="callout callout-{callout_type}" style="{container_style}">
<p class="callout-title" style="{title_style}">{title}</p>
<div class="callout-content" style="{content_style}">

{content}

</div>
</div>"""
