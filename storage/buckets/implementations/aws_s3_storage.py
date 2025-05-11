from src.services import S3FileManager
from storage.buckets import BucketStorage


class AmazonS3Adapter(BucketStorage):
    def __init__(self):
        self.bucket_s3 = S3FileManager()

    def upload(self, local_path: str, key: str) -> str:
        self.bucket_s3.upload(local_path, key)
        return self.bucket_s3.get_url()

    def delete(self, key: str) -> bool:
        return self.bucket_s3.delete(key)
