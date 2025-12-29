"""
md2epub - Obsidian Markdown to EPUB Converter

Convert Obsidian markdown notes to EPUB format with full support for
Obsidian-specific features like callouts, wikilinks, and embeds.
"""

__version__ = "0.1.0"

from .converter import convert_to_epub

__all__ = ["convert_to_epub", "__version__"]
