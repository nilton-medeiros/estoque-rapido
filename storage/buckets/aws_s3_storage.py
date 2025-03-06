from src.services.aws.s3_file_manager import S3FileManager
from storage.data.contracts.bucket_storage import BucketStorage


class AmazonS3Adapter(BucketStorage):
    def __init__(self):
        self.bucket_s3 = S3FileManager()

    async def upload(self, local_path: str, key: str) -> str:
        await self.bucket_s3.upload(local_path, key)
        return self.bucket_s3.get_url()
