"""OCI Functions entry point for the Image Resize API.

This module wraps the Flask application for deployment as an OCI Function.
The Fn Project invokes the handler function via fdk-python.
"""

import io
import json

from fdk import response

from app import create_app


# Create the Flask app once (cold start)
flask_app = create_app()


def handler(ctx, data: io.BytesIO = None):
    """OCI Functions handler.

    Routes incoming function invocations to the Flask application.
    Supports both direct invocation and API Gateway integration.
    """
    try:
        body = data.getvalue()

        # Parse the incoming request context from API Gateway
        headers = dict(ctx.Headers() or {})
        method = headers.get("Fn-Http-Method", "POST").upper()
        request_url = headers.get("Fn-Http-Request-Url", "/api/resize")

        # Build a WSGI-like environment for Flask
        with flask_app.test_request_context(
            path=request_url,
            method=method,
            headers=headers,
            data=body,
            content_type=headers.get("Content-Type", "application/octet-stream"),
        ):
            rv = flask_app.full_dispatch_request()
            resp_data = rv.get_data(as_text=True)
            resp_status = rv.status_code
            resp_headers = dict(rv.headers)

        return response.Response(
            ctx,
            response_data=resp_data,
            headers=resp_headers,
            status_code=resp_status,
        )
    except Exception as e:
        return response.Response(
            ctx,
            response_data=json.dumps({"error": str(e), "code": "FUNCTION_ERROR"}),
            headers={"Content-Type": "application/json"},
            status_code=500,
        )
