from storage.data.contracts.bucket_storage import BucketStorage


class BucketService:
    def __init__(self, adapter: BucketStorage):
        self.adapter = adapter

    async def upload(self, local_path: str, key: str):
        return await self.adapter.upload(local_path, key)
