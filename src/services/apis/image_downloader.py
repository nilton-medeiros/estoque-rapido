import logging
import os
import requests
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from src.shared.utils import get_uuid
from src.shared.utils.find_project_path import find_project_root

logger = logging.getLogger(__name__)


class ImageDownloader:
    """
    Classe responsável por fazer o download de imagens a partir de URLs e salvá-las temporariamente
    no diretório uploads/ do projeto para posterior upload ao bucket.
    """

    def __init__(self, timeout: int = 10, max_file_size: int = 5 * 1024 * 1024):
        """
        Inicializa o downloader de imagens.

        Args:
            timeout: Timeout em segundos para requisições HTTP (padrão: 10s)
            max_file_size: Tamanho máximo do arquivo em bytes (padrão: 5MB)
        """
        self.timeout = timeout
        self.max_file_size = max_file_size
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.svg', '.webp'}
        self.allowed_mime_types = {
            'image/jpeg', 'image/jpg', 'image/png',
            'image/svg+xml', 'image/webp'
        }

        # Headers para simular um navegador real
        self.headers = {
            'User-Agent': 'EstoqueRapidoApp/1.0 Image-Downloader',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _validate_url(self, url: str) -> bool:
        """
        Valida se a URL é válida e segura.

        Args:
            url: URL a ser validada

        Returns:
            True se a URL for válida, False caso contrário
        """
        try:
            parsed = urlparse(url)

            # Verifica se tem esquema e netloc
            if not parsed.scheme or not parsed.netloc:
                logger.warning(f"URL inválida - esquema ou netloc ausente: {url}")
                return False

            # Apenas HTTPS para segurança (APIs confiáveis)
            if parsed.scheme.lower() not in ['https', 'http']:
                logger.warning(f"URL com esquema não permitido: {parsed.scheme}")
                return False

            return True

        except Exception as e:
            logger.error(f"Erro ao validar URL {url}: {e}")
            return False

    def _get_file_extension_from_url(self, url: str) -> str:
        """
        Extrai a extensão do arquivo da URL.

        Args:
            url: URL da imagem

        Returns:
            Extensão do arquivo (ex: '.jpg', '.png')
        """
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Tenta obter extensão do path da URL
        _, ext = os.path.splitext(path)

        if ext in self.allowed_extensions:
            return ext

        # Se não conseguir da URL, assume .jpg como padrão
        logger.info(f"Não foi possível determinar extensão da URL {url}, usando .jpg como padrão")
        return '.jpg'

    def _get_file_extension_from_content_type(self, content_type: str) -> str:
        """
        Determina a extensão do arquivo baseada no Content-Type.

        Args:
            content_type: Content-Type retornado pelo servidor

        Returns:
            Extensão do arquivo baseada no MIME type
        """
        content_type = content_type.lower().split(';')[0].strip()

        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/svg+xml': '.svg',
            'image/webp': '.webp'
        }

        return mime_to_ext.get(content_type, '.jpg')

    def _create_uploads_dir(self) -> Path:
        """
        Cria o diretório uploads/ se não existir.

        Returns:
            Path para o diretório uploads
        """
        project_root = find_project_root(__file__)
        uploads_dir = project_root / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        return uploads_dir

    def download_image(self, image_url: str, prefix: str = "downloaded_img") -> Optional[str]:
        """
        Faz o download de uma imagem da URL e salva no diretório uploads/.

        Args:
            image_url: URL da imagem a ser baixada
            prefix: Prefixo para o nome do arquivo (padrão: "downloaded_img")

        Returns:
            Caminho relativo do arquivo salvo (ex: "uploads/downloaded_img_uuid.jpg")
            ou None em caso de erro
        """
        if not self._validate_url(image_url):
            return None

        try:
            logger.info(f"Iniciando download da imagem: {image_url}")

            # Faz a requisição com stream=True para controlar o tamanho
            response = requests.get(
                image_url,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            # Verifica o Content-Type
            content_type = response.headers.get('content-type', '').lower()
            if not any(mime in content_type for mime in self.allowed_mime_types):
                logger.warning(f"Content-Type não suportado: {content_type} para URL: {image_url}")
                return None

            # Verifica o tamanho do arquivo
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                logger.warning(f"Arquivo muito grande ({content_length} bytes) para URL: {image_url}")
                return None

            # Determina a extensão do arquivo
            file_extension = self._get_file_extension_from_content_type(content_type)
            if not file_extension:
                file_extension = self._get_file_extension_from_url(image_url)

            # Cria o diretório uploads se não existir
            uploads_dir = self._create_uploads_dir()

            # Gera nome único para o arquivo
            file_uuid = get_uuid()
            filename = f"{prefix}_{file_uuid}{file_extension}"
            file_path = uploads_dir / filename

            # Faz o download e salva o arquivo
            total_size = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filtrar chunks vazios
                        total_size += len(chunk)

                        # Verifica se não excedeu o tamanho máximo durante o download
                        if total_size > self.max_file_size:
                            f.close()
                            try:
                                os.remove(file_path)
                            except:
                                pass
                            logger.warning(f"Download cancelado - arquivo muito grande: {image_url}")
                            return None

                        f.write(chunk)

            # Verifica se o arquivo foi salvo com sucesso
            if not file_path.exists() or file_path.stat().st_size == 0:
                logger.error(f"Falha ao salvar arquivo ou arquivo vazio: {file_path}")
                try:
                    os.remove(file_path)
                except:
                    pass
                return None

            logger.info(f"Imagem baixada com sucesso: {filename} ({total_size} bytes)")

            # Retorna o caminho relativo (como esperado pelo resto do código)
            return f"uploads/{filename}"

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 'N/A'
            logger.error(f"Erro HTTP ({status_code}) ao baixar imagem {image_url}: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão ao baixar imagem {image_url}: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout ao baixar imagem {image_url}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição ao baixar imagem {image_url}: {e}")
        except OSError as e:
            logger.error(f"Erro de I/O ao salvar imagem {image_url}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao baixar imagem {image_url}: {e}")

        return None

    def download_and_validate_image(self, image_url: str, prefix: str = "downloaded_img") -> Tuple[Optional[str], bool]:
        """
        Faz o download da imagem e retorna informações sobre o sucesso da operação.

        Args:
            image_url: URL da imagem a ser baixada
            prefix: Prefixo para o nome do arquivo

        Returns:
            Tupla contendo (caminho_do_arquivo, sucesso)
            - caminho_do_arquivo: Caminho relativo do arquivo salvo ou None
            - sucesso: True se o download foi bem-sucedido, False caso contrário
        """
        downloaded_file = self.download_image(image_url, prefix)
        return downloaded_file, downloaded_file is not None


# Função utilitária para uso direto (mantém compatibilidade com código existente)
def download_image_from_url(image_url: str, prefix: str = "downloaded_img") -> Optional[str]:
    """
    Função utilitária para fazer download de uma imagem.

    Args:
        image_url: URL da imagem
        prefix: Prefixo do nome do arquivo

    Returns:
        Caminho relativo do arquivo baixado ou None em caso de erro
    """
    downloader = ImageDownloader()
    return downloader.download_image(image_url, prefix)