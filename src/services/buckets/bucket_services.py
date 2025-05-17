from typing import Any
from storage.buckets import BucketStorage


class BucketServices:
    def __init__(self, adapter: BucketStorage):
        self.adapter = adapter

    def upload(self, local_path: str, key: str) -> str|Any:
        return self.adapter.upload(local_path, key)

    def delete(self, key: str) -> bool:
        return self.adapter.delete(key)
