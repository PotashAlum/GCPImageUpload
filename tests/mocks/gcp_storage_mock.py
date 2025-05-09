# tests/mocks/gcp_storage_mock.py
import io
from datetime import datetime, timedelta
from urllib.parse import urljoin

class MockBlob:
    """Mock implementation of Google Cloud Storage Blob"""
    
    def __init__(self, name, bucket):
        self.name = name
        self.bucket = bucket
        self._file_content = None
        self._content_type = None
    
    def upload_from_file(self, file_obj, content_type=None):
        """Mock uploading a file to the blob"""
        file_obj.seek(0)
        self._file_content = file_obj.read()
        self._content_type = content_type
        file_obj.seek(0)  # Reset file position for potential future reads
    
    def download_as_bytes(self):
        """Mock downloading blob content as bytes"""
        return self._file_content
    
    def download_as_string(self):
        """Mock downloading blob content as string"""
        return self._file_content.decode('utf-8') if self._file_content else ""
    
    def generate_signed_url(self, version="v4", expiration=None, method="GET"):
        """Mock generating a signed URL for the blob"""
        host = "https://storage.example.com"
        path = f"/{self.bucket.name}/{self.name}"
        query = f"?signed=true&expires={datetime.now() + expiration}&method={method}"
        return urljoin(host, path) + query
    
    def delete(self):
        """Mock deleting the blob"""
        if self.name in self.bucket._blobs:
            del self.bucket._blobs[self.name]
        self._file_content = None
        self._content_type = None


class MockBucket:
    """Mock implementation of Google Cloud Storage Bucket"""
    
    def __init__(self, name):
        self.name = name
        self._blobs = {}
    
    def blob(self, name):
        """Get a blob from the bucket, creating it if it doesn't exist"""
        if name not in self._blobs:
            self._blobs[name] = MockBlob(name, self)
        return self._blobs[name]
    
    def list_blobs(self, prefix=None):
        """List blobs in the bucket, optionally filtered by prefix"""
        if prefix:
            return [blob for name, blob in self._blobs.items() if name.startswith(prefix)]
        return list(self._blobs.values())


class MockStorageClient:
    """Mock implementation of Google Cloud Storage Client"""
    
    def __init__(self):
        self._buckets = {}
    
    def bucket(self, name):
        """Get a bucket, creating it if it doesn't exist"""
        if name not in self._buckets:
            self._buckets[name] = MockBucket(name)
        return self._buckets[name]
    
    def list_buckets(self):
        """List all buckets"""
        return list(self._buckets.values())
    
    def create_bucket(self, name):
        """Create a new bucket"""
        if name not in self._buckets:
            self._buckets[name] = MockBucket(name)
        return self._buckets[name]


# Usage in tests:
# from tests.mocks.gcp_storage_mock import MockStorageClient
# storage_client = MockStorageClient()
# bucket = storage_client.bucket("test-bucket")
