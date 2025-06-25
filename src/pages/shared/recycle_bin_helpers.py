import datetime
import math
from typing import Any


def get_deleted_info_message(entity: Any) -> str:
    """
    Gera uma mensagem de informação para uma entidade com status 'DELETED'.
    Calcula os dias restantes para exclusão permanente.

    Args:
        entity: O objeto da entidade. Deve ter o atributo 'deleted_at'.

    Returns:
        str: A mensagem de informação formatada.
    """
    if hasattr(entity, 'deleted_at') and entity.deleted_at:
        # Data em que o item foi movido para a lixeira (presumivelmente UTC)
        data_movido_lixeira = entity.deleted_at

        # Data final para exclusão permanente (90 dias após mover para lixeira)
        data_exclusao_permanente = data_movido_lixeira + datetime.timedelta(days=90)

        # Data e hora atuais em UTC para comparação consistente
        agora_utc = datetime.datetime.now(datetime.UTC)

        # Calcula o tempo restante até a exclusão permanente
        tempo_restante = data_exclusao_permanente - agora_utc

        days_left = 0  # Valor padrão caso o tempo já tenha expirado
        if tempo_restante.total_seconds() > 0:
            dias_restantes_float = tempo_restante.total_seconds() / (24 * 60 * 60)
            days_left = math.ceil(dias_restantes_float)

        if days_left == 0:
            return "A exclusão permanente está prevista para hoje ou já pode ter ocorrido."
        elif days_left == 1:
            return f"A exclusão automática e permanente do banco de dados ocorrerá em {days_left} dia."
        else:
            return f"A exclusão automática e permanente do banco de dados ocorrerá em {days_left} dias."
    else:
        # Caso deleted_at não esteja definido
        return "Este registro está na lixeira, mas a data de início da contagem para exclusão não foi registrada."