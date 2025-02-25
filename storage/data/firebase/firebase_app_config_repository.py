from src.domain.models.app_config import AppConfig
from src.utils.deep_translator import deepl_translator
from storage.data.interfaces.app_config_repository import AppConfigRepository

from storage.data.firebase.firebase_initialize import get_firebase_app
from firebase_admin import firestore
from firebase_admin import exceptions


class FirebaseAppConfigRepository(AppConfigRepository):
    """
    Implementação concreta de um repositório de configurações de aplicativo
    que utiliza o Firebase como fonte de dados.
    """

    def __init__(self):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'app_config'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """

        get_firebase_app()

        self.db = firestore.client()
        self.collection = self.db.collection('app_config')

    async def get(self, config_id: str) -> AppConfig:
        """
        Encontrar uma configuração do sistema (app_config) pelo seu identificador único.

        Args:
            config_id (str): O identificador único do app_config.

        Retorna:
            Optional[AppConfig]: Uma instância da app_config se encontrada, None caso contrário.
        """
        try:
            doc = self.collection.document(config_id).get()
            if doc.exists:
                app_data = doc.to_dict()
                app_data['id'] = doc.id
                return self._doc_to_config(app_data)
            else:
                print('Documento não encontrado!')
        except Exception as e:
            print(f'Erro ao buscar documento: {e}')

        return None

    async def save(self, config: AppConfig) -> str:
        """
        Salvar um config no banco de dados Firestore.

        Se o config já existir pelo seu id, atualiza o documento existente em vez
        de criar um novo.

        Args:
            config (AppConfig): A instância do config a ser salvo.

        Retorna:
            str: O ID do documento do config salvo.
        """
        try:
            config_dict = self._config_to_dict(config)

            if not config.id:
                config.id = 'settings'  # Considerar gerar um ID único ou usar outro campo

            doc_ref = self.collection.document(config.id)
            # Usar set com merge para criar ou atualizar para evitar erros de campo ausente
            doc_ref.set(config_dict, merge=True)

            return doc_ref.id  # Retornar o ID real do documento

        except exceptions.FirebaseError as e:
            # Registrar o erro em um sistema de log com contexto e mensagem original
            # Manter mensagem original para depuração
            print(f"Erro ao salvar configuração do sistema: {e}")
            raise  # Re-lançar o erro original

        except Exception as e:
            # Registrar o erro em um sistema de log com contexto e mensagem original
            # Manter mensagem original para depuração
            print(f"Erro inesperado ao salvar configuração do sistema: {e}")
            raise  # Re-lançar o erro original

    def delete(self, config_id: str) -> bool:
        """
        Excluir uma configuração do sistema pelo seu identificador único do Firestore.

        Args:
            config_id (str): O identificador único da configuração.

        Retorna:
            bool: True se a exclusão for bem-sucedida, False caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a exclusão.
        """
        try:
            # Deleta do Firestore
            self.collection.document(config_id).delete()
            return True
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao deletar a configuração de sistema com id '{config_id}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao deletar configuração de sistema com id '{config_id}': {str(e)}")


    def _config_to_dict(self, config: AppConfig) -> dict:
        # Converte o objeto datetime do python para o Timestamp do Firestore
        timestamp_expires_in = firestore.Timestamp.from_datetime(config.dfe_api_token_expires_in)

        config_dict = {
            'id': config.id,
            'dfe_api_token': config.dfe_api_token,
            'dfe_api_token_expires_in': timestamp_expires_in,
        }

        return config_dict

    def _doc_to_config(self, doc: dict) -> AppConfig:
        # Converte o Timestamp do Firestore para o objeto datetime do Python
        timestamp_expires_in = doc['dfe_api_token_expires_in']
        datetime_expires_in = timestamp_expires_in.to_datetime()

        return AppConfig(
            id=doc['id'],
            dfe_api_token=doc['dfe_api_token'],
            dfe_api_token_expires_in=datetime_expires_in,
        )
