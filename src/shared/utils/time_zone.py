# Adicionado para tipagem, embora pytz lide com datetime
from datetime import datetime
import pytz  # Adicionado para manipulação de fuso horário

# Função para formatar datetime para UTC-3 e no formato desejado


def format_datetime_to_utc_minus_3(dt_object: datetime | None = None) -> str:
    if dt_object is None:
        return "N/A"  # Ou uma string vazia, como preferir

    # Garante que o datetime está em UTC
    if dt_object.tzinfo is None or dt_object.tzinfo.utcoffset(dt_object) is None:
        # Se for naive (sem informação de fuso), assume que é UTC
        dt_utc = pytz.utc.localize(dt_object)
    else:
        # Se já tem informação de fuso, converte para UTC para garantir consistência
        dt_utc = dt_object.astimezone(pytz.utc)

    # Define o fuso horário UTC-3 (Horário de Brasília padrão, sem considerar horário de verão)
    utc_minus_3_tz = pytz.FixedOffset(-3 * 60)  # -3 horas * 60 minutos/hora

    # Converte para UTC-3 e formata
    return dt_utc.astimezone(utc_minus_3_tz).strftime("%d/%m/%Y %H:%M:%S")
