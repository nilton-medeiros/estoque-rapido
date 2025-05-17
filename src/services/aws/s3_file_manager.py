import boto3
import os

# import boto3.exceptions
from botocore.exceptions import ClientError
from dotenv import load_dotenv


class S3FileManager:
    """
    Gerenciador de arquivos para o Amazon S3.

    Esta classe fornece métodos para gerenciar operações básicas de arquivos no Amazon S3,
    incluindo upload, deleção e verificação de existência de arquivos.

    Attributes:
        s3_client: Cliente boto3 para interação com o S3.
        bucket (str): Nome do bucket S3 onde os arquivos serão armazenados.
        prefix (str): Prefixo padrão para todas as operações no bucket.
    """

    def __init__(self):
        """
        Inicializa o gerenciador de arquivos S3 com as configurações padrão.

        O cliente S3 é configurado usando as credenciais padrão do ambiente.
        O bucket e o prefixo são definidos com valores predeterminados.
        """
        load_dotenv()

        self.region_name = os.getenv('AWS_DEFAULT_REGION')
        self.bucket = os.getenv('AWS_BUCKET')

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region_name,
        )

        self.prefix = 'estoquerapido/public'
        self._relativ_key = ''

    def get_url(self) -> str:
        """
        Constrói a url completa do arquivo no S3.

        Args: None

        Returns:
            str: URL completa.

        Example:
            Para key="pasta/arquivo.txt" e prefix="estoquerapido/public",
            retorna "https://<bucket>.s3.<region>.amazonaws.com/estoquerapido/public/pasta/arquivo.txt"
        """
        return f"https://{self.bucket}.s3.{self.region_name}.amazonaws.com/{self._relativ_key}"

    def _get_full_key(self, key: str) -> str:
        """
        Constrói a chave completa para o arquivo no S3.

        Args:
            key (str): Chave relativa do arquivo.

        Returns:
            str: Chave completa incluindo o prefixo configurado.

        Example:
            Para key="pasta/arquivo.txt" e prefix="estoquerapido/public",
            retorna "estoquerapido/public/pasta/arquivo.txt"
        """
        clean_key = key.lstrip('/')
        self._relativ_key = f"{self.prefix}/{clean_key}"
        return self._relativ_key

    def upload(self, local_path: str, key: str):
        """
        Faz upload de um arquivo local para o S3.

        Args:
            local_path (str): Caminho completo do arquivo local a ser enviado.
            key (str): Chave relativa onde o arquivo será armazenado no S3.

        Raises:
            boto3.exceptions.S3UploadFailedError: Se o upload falhar.
            FileNotFoundError: Se o arquivo local não for encontrado.

        Example:
            >>> s3_manager = S3FileManager()
            >>> s3_manager.upload('/path/local/arquivo.txt', 'pasta/arquivo.txt')
        """
        full_key = self._get_full_key(key)
        self.s3_client.upload_file(local_path, self.bucket, full_key)

    def delete(self, key: str) -> bool:
        """
        Remove um arquivo do S3.

        Args:
            key (str): Chave relativa do arquivo a ser removido.

        Raises:
            ClientError: Se ocorrer um erro durante a deleção do arquivo.

        Example:
            >>> s3_manager = S3FileManager()
            >>> s3_manager.delete('pasta/arquivo.txt')
        """
        full_key = self._get_full_key(key)
        try:
            response = self.s3_client.delete_object(Bucket=self.bucket, Key=full_key)
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            if status_code == 204:
                return True
            else:
                return False
        except ClientError as e:
            return False


    def exists(self, key: str) -> bool:
        """
        Verifica se um arquivo existe no S3.

        Args:
            key (str): Chave relativa do arquivo a ser verificado.

        Returns:
            bool: True se o arquivo existe, False caso contrário.

        Raises:
            ClientError: Se ocorrer um erro diferente de 404 durante a verificação.

        Example:
            >>> s3_manager = S3FileManager()
            >>> if s3_manager.exists('pasta/arquivo.txt'):
            ...     print("Arquivo existe")
        """
        full_key = self._get_full_key(key)
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=full_key)
            return True
        except ClientError as e:
            # O arquivo não existe: status 404
            if e.response['Error']['Code'] == '404':
                return False
            raise


# Exemplo de uso
"""
if __name__ == "__main__":
    s3_manager = S3FileManager()

    # Upload de arquivo
    s3_manager.upload('arquivo_local.txt', 'documentos/arquivo.txt')

    # Verificação de existência
    if s3_manager.exists('documentos/arquivo.txt'):
        print("Arquivo existe no S3")

    # Deleção de arquivo
    s3_manager.delete('documentos/arquivo.txt')
"""
