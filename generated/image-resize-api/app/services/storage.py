"""Object Storage service abstraction.

Provides a local mock implementation for development/testing and an OCI
Object Storage client for production.
"""

import os


class LocalStorageClient:
    """In-memory storage client for local development and testing."""

    def __init__(self):
        self._store = {}  # {(namespace, bucket, object_name): data}

    def put_object(self, namespace, bucket, object_name, data):
        """Store an object in memory."""
        key = (namespace, bucket, object_name)
        self._store[key] = data

    def get_object(self, namespace, bucket, object_name):
        """Retrieve an object from memory."""
        key = (namespace, bucket, object_name)
        if key not in self._store:
            raise FileNotFoundError(f"Object not found: {namespace}/{bucket}/{object_name}")
        return self._store[key]

    def list_objects(self, namespace, bucket, prefix=""):
        """List objects with the given prefix."""
        results = []
        for ns, bkt, name in self._store:
            if ns == namespace and bkt == bucket and name.startswith(prefix):
                results.append(name)
        return sorted(results)


class OCIStorageClient:
    """OCI Object Storage client wrapper."""

    def __init__(self):
        import oci
        self._config = oci.config.from_file()
        self._client = oci.object_storage.ObjectStorageClient(self._config)

    def put_object(self, namespace, bucket, object_name, data):
        """Upload an object to OCI Object Storage."""
        self._client.put_object(
            namespace_name=namespace,
            bucket_name=bucket,
            object_name=object_name,
            put_object_body=data,
        )

    def get_object(self, namespace, bucket, object_name):
        """Download an object from OCI Object Storage."""
        response = self._client.get_object(
            namespace_name=namespace,
            bucket_name=bucket,
            object_name=object_name,
        )
        return response.data.content

    def list_objects(self, namespace, bucket, prefix=""):
        """List objects in a bucket."""
        response = self._client.list_objects(
            namespace_name=namespace,
            bucket_name=bucket,
            prefix=prefix,
        )
        return [obj.name for obj in response.data.objects]


# Singleton storage client
_storage_client = None


def get_storage_client(app=None):
    """Get the appropriate storage client based on environment.

    Uses LocalStorageClient for development/testing, OCIStorageClient
    when OCI_CONFIG_FILE is present.
    """
    global _storage_client

    # In testing mode, always return a fresh local client
    if app and app.config.get("TESTING"):
        return LocalStorageClient()

    if _storage_client is None:
        if os.environ.get("OCI_CONFIG_FILE") or os.path.exists(os.path.expanduser("~/.oci/config")):
            try:
                _storage_client = OCIStorageClient()
            except Exception:
                _storage_client = LocalStorageClient()
        else:
            _storage_client = LocalStorageClient()

    return _storage_client
