from storage.buckets.contracts.bucket_storage import BucketStorage


class BucketServices:
    def __init__(self, adapter: BucketStorage):
        self.adapter = adapter

    def upload(self, local_path: str, key: str):
        return self.adapter.upload(local_path, key)

    def delete(self, key: str):
        return self.adapter.delete(key)
