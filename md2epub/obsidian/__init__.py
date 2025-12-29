"""
Obsidian-specific markdown processing.

This module handles Obsidian-specific syntax like callouts, wikilinks,
embeds, and frontmatter parsing.
"""

from .frontmatter import parse_frontmatter, extract_frontmatter, Frontmatter
from .callouts import convert_callouts, CALLOUT_STYLES
from .wikilinks import convert_wikilinks
from .embeds import convert_embeds

__all__ = [
    "parse_frontmatter",
    "extract_frontmatter",
    "Frontmatter",
    "convert_callouts",
    "CALLOUT_STYLES",
    "convert_wikilinks",
    "convert_embeds",
]
