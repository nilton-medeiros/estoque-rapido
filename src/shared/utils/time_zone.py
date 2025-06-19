# Adicionado para tipagem, embora pytz lide com datetime
from datetime import datetime
import pytz  # Adicionado para manipulação de fuso horário

# Nomes em português para dias da semana e meses
DIAS_SEMANA_PT = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo"
]
MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Função para formatar datetime para UTC-3 e no formato desejado


def format_datetime_to_utc_minus_3(dt_object: datetime | None = None, format_str: str = "%d/%m/%Y %H:%M:%S") -> str:
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

    # Converte para UTC-3
    dt_local = dt_utc.astimezone(utc_minus_3_tz)

    # Processa a string de formato para substituir %A e %B por nomes em português
    # Isso garante que os nomes sejam em português, independentemente do locale do sistema.
    processed_format_str = format_str

    if "%A" in processed_format_str:
        # Escapa '%' nos nomes dos dias/meses caso eles contenham '%', para strftime
        weekday_name = DIAS_SEMANA_PT[dt_local.weekday()].replace('%', '%%')
        processed_format_str = processed_format_str.replace("%A", weekday_name)

    if "%B" in processed_format_str:
        month_name = MESES_PT[dt_local.month - 1].replace('%', '%%')
        processed_format_str = processed_format_str.replace("%B", month_name)

    # Formata usando a string processada
    return dt_local.strftime(processed_format_str)
