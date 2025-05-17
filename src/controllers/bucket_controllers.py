import logging

from src.services import BucketServices
from storage.buckets.implementations.aws_s3_storage import AmazonS3Adapter
import boto3

logger = logging.getLogger(__name__)

def handle_upload_bucket(local_path: str, key: str) -> str:
    """
    Este handle utiliza o adaptador AmazonS3Adapter para o BucketService,
    posteriormente se quiser mudar o storage para Azure ou Google, é só trocar o adaptador
    que deverá seguir o contrato da classe abstrata BucketStorage.
    """
    adapter = AmazonS3Adapter()
    bucket_services = BucketServices(adapter)

    try:
        storage_url: str = bucket_services.upload(local_path, key)
        logger.info(f"Arquivo enviado com sucesso para o bucket: {storage_url}")
        return storage_url
    except FileNotFoundError:
        raise ValueError(f"O arquivo {local_path} não foi encontrado.")
    except boto3.exceptions.S3UploadFailedError as e: # type: ignore
        raise RuntimeError(f"Falha ao fazer upload para o Bucket de armazenamento: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Erro inesperado ao fazer upload: {str(e)}")

def handle_delete_bucket(key: str) -> bool:
    adapter = AmazonS3Adapter()
    bucket_services = BucketServices(adapter)

    try:
        is_deleted: bool = bucket_services.delete(key)
        logger.info(f"Arquivo {'deletado' if is_deleted else 'não pode ser deletado'} do bucket: {key}")
        return is_deleted
    except Exception as e:
        raise RuntimeError(f"Ocorreu um erro: {e}")
