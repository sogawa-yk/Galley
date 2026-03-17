"""Image Resize API - Flask application for OCI Functions deployment."""

import os

from flask import Flask


def create_app(testing=False):
    """Application factory for the Image Resize API."""
    app = Flask(__name__)

    app.config["TESTING"] = testing
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

    # Object Storage configuration
    app.config["OCI_NAMESPACE"] = os.environ.get("OCI_NAMESPACE", "demo-namespace")
    app.config["OCI_BUCKET_INPUT"] = os.environ.get("OCI_BUCKET_INPUT", "input-images")
    app.config["OCI_BUCKET_OUTPUT"] = os.environ.get("OCI_BUCKET_OUTPUT", "output-images")
    app.config["OCI_REGION"] = os.environ.get("OCI_REGION", "ap-tokyo-1")

    # Register health endpoint
    @app.route("/health")
    def health():
        return {"status": "ok"}

    # Register routes
    from routes.resize import resize_bp
    app.register_blueprint(resize_bp)

    return app


# For local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)
