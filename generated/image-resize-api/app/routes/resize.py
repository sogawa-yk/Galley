"""Image resize API routes."""

import io
import uuid

from flask import Blueprint, current_app, jsonify, request

from services.image_processor import ImageProcessor
from services.storage import get_storage_client

resize_bp = Blueprint("resize", __name__)

ALLOWED_FORMATS = {"jpeg", "jpg", "png", "webp"}
DEFAULT_QUALITY = 85
MAX_DIMENSION = 4096


@resize_bp.route("/api/resize", methods=["POST"])
def resize_image():
    """Resize an uploaded image and store the result in Object Storage.

    Form parameters:
        file: Image file (JPEG, PNG, or WebP)
        width: Target width in pixels (optional, 1-4096)
        height: Target height in pixels (optional, 1-4096)
        quality: Output quality 1-100 (optional, default 85)
        output_format: Output format - jpeg, png, webp (optional, preserves original)
    """
    # Validate file presence
    if "file" not in request.files:
        return jsonify({"error": "No file provided", "code": "MISSING_FILE"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected", "code": "EMPTY_FILENAME"}), 400

    # Validate file extension
    ext = _get_extension(file.filename)
    if ext not in ALLOWED_FORMATS:
        return jsonify({
            "error": f"Unsupported format: {ext}. Allowed: {', '.join(sorted(ALLOWED_FORMATS))}",
            "code": "UNSUPPORTED_FORMAT"
        }), 400

    # Parse resize parameters
    width = request.form.get("width", type=int)
    height = request.form.get("height", type=int)
    quality = request.form.get("quality", default=DEFAULT_QUALITY, type=int)
    output_format = request.form.get("output_format", "").lower()

    # Validate dimensions
    if width is not None and (width < 1 or width > MAX_DIMENSION):
        return jsonify({"error": f"Width must be between 1 and {MAX_DIMENSION}", "code": "INVALID_WIDTH"}), 400
    if height is not None and (height < 1 or height > MAX_DIMENSION):
        return jsonify({"error": f"Height must be between 1 and {MAX_DIMENSION}", "code": "INVALID_HEIGHT"}), 400
    if width is None and height is None:
        return jsonify({"error": "At least one of width or height is required", "code": "MISSING_DIMENSIONS"}), 400

    # Validate quality
    if quality < 1 or quality > 100:
        return jsonify({"error": "Quality must be between 1 and 100", "code": "INVALID_QUALITY"}), 400

    # Validate output format
    if output_format and output_format not in ALLOWED_FORMATS:
        return jsonify({
            "error": f"Unsupported output format: {output_format}",
            "code": "UNSUPPORTED_OUTPUT_FORMAT"
        }), 400

    # Read image data
    image_data = file.read()

    try:
        # Process image
        processor = ImageProcessor()
        result_data, result_format = processor.resize(
            image_data=image_data,
            width=width,
            height=height,
            quality=quality,
            output_format=output_format or None,
        )
    except ValueError as e:
        return jsonify({"error": str(e), "code": "PROCESSING_ERROR"}), 400
    except Exception as e:
        return jsonify({"error": "Image processing failed", "code": "INTERNAL_ERROR"}), 500

    # Generate object names
    request_id = uuid.uuid4().hex[:12]
    original_name = file.filename or "image"
    base_name = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
    input_key = f"uploads/{request_id}/{original_name}"
    output_key = f"resized/{request_id}/{base_name}.{result_format}"

    # Store to Object Storage
    storage = get_storage_client(current_app)
    try:
        storage.put_object(
            namespace=current_app.config["OCI_NAMESPACE"],
            bucket=current_app.config["OCI_BUCKET_INPUT"],
            object_name=input_key,
            data=image_data,
        )
        storage.put_object(
            namespace=current_app.config["OCI_NAMESPACE"],
            bucket=current_app.config["OCI_BUCKET_OUTPUT"],
            object_name=output_key,
            data=result_data,
        )
    except Exception as e:
        return jsonify({"error": "Storage operation failed", "code": "STORAGE_ERROR"}), 500

    return jsonify({
        "status": "success",
        "request_id": request_id,
        "original": {
            "filename": original_name,
            "size_bytes": len(image_data),
            "storage_key": input_key,
        },
        "resized": {
            "format": result_format,
            "size_bytes": len(result_data),
            "storage_key": output_key,
            "width": width,
            "height": height,
            "quality": quality,
        },
    }), 200


def _get_extension(filename):
    """Extract lowercase file extension."""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()
