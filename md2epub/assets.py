"""
Asset handling for EPUB generation.

Manages images and other assets from the Obsidian vault,
preparing them for embedding in the EPUB.
"""

import mimetypes
import re
from pathlib import Path

from PIL import Image


# Supported image formats for EPUB
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".svg"}

# Maximum image dimensions for e-readers (reMarkable and iBooks friendly)
MAX_WIDTH = 1404  # reMarkable 2 width
MAX_HEIGHT = 1872  # reMarkable 2 height


class AssetManager:
    """Manages assets (images) for EPUB generation."""

    def __init__(self, vault_root: Path | None = None):
        """
        Initialize the asset manager.

        Args:
            vault_root: Root directory of the Obsidian vault.
        """
        self.vault_root = vault_root
        self._assets: dict[str, bytes] = {}
        self._path_map: dict[str, str] = {}

    def resolve_image_path(
        self,
        image_ref: str,
        source_file: Path | None = None,
    ) -> Path | None:
        """
        Resolve an image reference to an actual file path.

        Obsidian allows relative paths and also searches the vault.

        Args:
            image_ref: The image reference from the markdown.
            source_file: The source markdown file for relative paths.

        Returns:
            Resolved Path or None if not found.
        """
        # Try as absolute path first
        if Path(image_ref).is_absolute() and Path(image_ref).exists():
            return Path(image_ref)

        # Try relative to source file
        if source_file:
            relative_path = source_file.parent / image_ref
            if relative_path.exists():
                return relative_path

        # Try relative to vault root
        if self.vault_root:
            vault_path = self.vault_root / image_ref
            if vault_path.exists():
                return vault_path

            # Search in common Obsidian attachment folders
            for folder in ["attachments", "assets", "images", "media", ""]:
                search_path = self.vault_root / folder / Path(image_ref).name
                if search_path.exists():
                    return search_path

        return None

    def add_image(
        self,
        image_ref: str,
        source_file: Path | None = None,
        optimize: bool = True,
    ) -> str | None:
        """
        Add an image to the asset collection.

        Args:
            image_ref: The image reference from markdown.
            source_file: The source markdown file.
            optimize: Whether to optimize the image for e-readers.

        Returns:
            The EPUB resource path for the image, or None if not found.
        """
        # Check if already processed
        if image_ref in self._path_map:
            return self._path_map[image_ref]

        # Resolve the actual file path
        image_path = self.resolve_image_path(image_ref, source_file)
        if not image_path:
            return None

        # Generate EPUB-safe filename
        epub_filename = self._safe_filename(image_path.name)
        epub_path = f"images/{epub_filename}"

        # Read and optionally optimize the image
        try:
            image_data = self._process_image(image_path, optimize)
            self._assets[epub_path] = image_data
            self._path_map[image_ref] = epub_path
            return epub_path
        except Exception:
            return None

    def _process_image(self, path: Path, optimize: bool) -> bytes:
        """Read and optionally optimize an image."""
        if path.suffix.lower() == ".svg":
            # SVG: just read as-is
            return path.read_bytes()

        if not optimize:
            return path.read_bytes()

        # Open with Pillow for optimization
        with Image.open(path) as img:
            # Convert RGBA to RGB if needed (for JPEG)
            if img.mode == "RGBA" and path.suffix.lower() in (".jpg", ".jpeg"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background

            # Resize if too large
            if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
                img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

            # Save to bytes
            from io import BytesIO
            buffer = BytesIO()

            if path.suffix.lower() == ".png":
                img.save(buffer, format="PNG", optimize=True)
            elif path.suffix.lower() in (".jpg", ".jpeg"):
                img.save(buffer, format="JPEG", quality=85, optimize=True)
            elif path.suffix.lower() == ".gif":
                img.save(buffer, format="GIF")
            else:
                # Default to PNG
                img.save(buffer, format="PNG")

            return buffer.getvalue()

    def _safe_filename(self, filename: str) -> str:
        """Create an EPUB-safe filename."""
        # Remove special characters, keep extension
        name = Path(filename).stem
        ext = Path(filename).suffix.lower()

        # Replace unsafe characters
        safe_name = re.sub(r"[^\w\-]", "_", name)

        # Ensure uniqueness
        counter = 1
        final_name = f"{safe_name}{ext}"
        while final_name in [Path(p).name for p in self._assets]:
            final_name = f"{safe_name}_{counter}{ext}"
            counter += 1

        return final_name

    def get_assets(self) -> dict[str, bytes]:
        """Get all collected assets."""
        return self._assets.copy()

    def get_mime_type(self, path: str) -> str:
        """Get the MIME type for an asset path."""
        mime_type, _ = mimetypes.guess_type(path)
        return mime_type or "application/octet-stream"

    def update_html_paths(self, html: str) -> str:
        """
        Update image paths in HTML to use EPUB resource paths.

        Args:
            html: HTML content with original image paths.

        Returns:
            HTML with updated image paths.
        """
        for original, epub_path in self._path_map.items():
            # Replace src="original" with src="epub_path"
            html = html.replace(f'src="{original}"', f'src="{epub_path}"')
            # Also handle URL-encoded versions
            import urllib.parse
            encoded = urllib.parse.quote(original)
            html = html.replace(f'src="{encoded}"', f'src="{epub_path}"')

        return html
