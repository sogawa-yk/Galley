"""Image processing service using Pillow."""

import io

from PIL import Image


# Map format names to Pillow format identifiers
FORMAT_MAP = {
    "jpeg": "JPEG",
    "jpg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
}

# Pillow format to file extension
FORMAT_TO_EXT = {
    "JPEG": "jpeg",
    "PNG": "png",
    "WEBP": "webp",
}


class ImageProcessor:
    """Handles image resizing operations."""

    def resize(self, image_data, width=None, height=None, quality=85, output_format=None):
        """Resize an image and return the result as bytes.

        Args:
            image_data: Raw image bytes.
            width: Target width (pixels). None to auto-calculate from height.
            height: Target height (pixels). None to auto-calculate from width.
            quality: Output quality 1-100 (applies to JPEG/WebP).
            output_format: Target format ('jpeg', 'png', 'webp'). None preserves original.

        Returns:
            Tuple of (result_bytes, format_extension_str).

        Raises:
            ValueError: If the image data is invalid or cannot be processed.
        """
        try:
            img = Image.open(io.BytesIO(image_data))
        except Exception:
            raise ValueError("Invalid image data: could not open image")

        original_width, original_height = img.size

        # Calculate target dimensions preserving aspect ratio
        if width and height:
            target_width, target_height = width, height
        elif width:
            ratio = width / original_width
            target_width = width
            target_height = max(1, round(original_height * ratio))
        elif height:
            ratio = height / original_height
            target_width = max(1, round(original_width * ratio))
            target_height = height
        else:
            raise ValueError("At least one of width or height must be specified")

        # Resize
        resized = img.resize((target_width, target_height), Image.LANCZOS)

        # Determine output format
        if output_format:
            pil_format = FORMAT_MAP.get(output_format.lower())
            if not pil_format:
                raise ValueError(f"Unsupported output format: {output_format}")
        else:
            # Preserve original format
            pil_format = img.format
            if pil_format not in FORMAT_TO_EXT:
                # Default to JPEG if original format is unknown
                pil_format = "JPEG"

        # Convert RGBA to RGB for JPEG (JPEG doesn't support alpha)
        if pil_format == "JPEG" and resized.mode in ("RGBA", "P"):
            resized = resized.convert("RGB")

        # Save to buffer
        output_buffer = io.BytesIO()
        save_kwargs = {}
        if pil_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
        if pil_format == "WEBP":
            save_kwargs["method"] = 4  # balanced compression speed

        resized.save(output_buffer, format=pil_format, **save_kwargs)
        result_bytes = output_buffer.getvalue()

        return result_bytes, FORMAT_TO_EXT[pil_format]
