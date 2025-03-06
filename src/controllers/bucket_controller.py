from src.services.buckets.bucket_service import BucketService
from storage.buckets.aws_s3_storage import AmazonS3Adapter
import boto3


async def handle_upload_bucket(local_path: str, key: str):
    """
    Este handle utiliza o adaptador AmazonS3Adapter para o BucketService,
    posteriormente se quiser mudar o storage para Azure ou Google, é só trocar o adaptador
    que deverá seguir o contrato da classe abstrata BucketStorage.
    """
    adapter = AmazonS3Adapter()
    bucket_service = BucketService(adapter)

    try:
        storage_url = await bucket_service.upload(local_path, key)
        return storage_url
    except FileNotFoundError:
        raise ValueError(f"O arquivo {local_path} não foi encontrado.")
    except boto3.exceptions.S3UploadFailedError as e:
        raise RuntimeError(f"Falha ao fazer upload para o S3: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Erro inesperado ao fazer upload: {str(e)}")
