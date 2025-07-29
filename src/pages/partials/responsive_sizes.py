from httpx import head


def get_responsive_sizes(page_width: int|float|None) -> dict[str, int|float]:
    """
    Versão com cálculo mais matemático/proporcional.

    Usa interpolação linear baseada na largura da tela para
    garantir transições mais suaves entre breakpoints.
    """
    width: int = 500
    if page_width:
        width = int(page_width)

    # Calcular fator de escala baseado nos breakpoints
    if width < 576:
        scale_factor = width / 576  # Escala baseada no mobile mínimo
    elif width < 768:
        scale_factor = 1 + (width - 576) / (768 - 576) * 0.3  # 12-16 font
    elif width < 992:
        scale_factor = 1.3 + (width - 768) / (992 - 768) * 0.3  # 16-18 font
    elif width < 1200:
        scale_factor = 1.6 + (width - 992) / (1200 - 992) * 0.3  # 18-20 font
    elif width < 1400:
        scale_factor = 1.9 + (width - 1200) / (1400 - 1200) * 0.3  # 20-22 font
    else:
        scale_factor = min(2.2, 2.2 + (width - 1400) / 1000 * 0.3)  # Cap no crescimento

    font_size = int(12 * scale_factor)
    title_size = int(font_size * 1.3)      # Para títulos principais (H2/H3)
    header_size = int(font_size * 1.5)     # Para cabeçalhos maiores (H1)

    return {
        "header_size": header_size,
        "title_size": title_size,
        "font_size": font_size,
        "icon_size": int(font_size * 1.2),  # Sempre 20% maior que font
        "button_width": min(int(width * (0.9 - scale_factor * 0.15)), 500),  # Diminui % conforme tela cresce
        "input_width": min(int(width * (0.9 - scale_factor * 0.15)), 500),
        "form_padding": int(4 + scale_factor * 8),  # Cresce de 4 até ~32
        "spacing": int(2 + scale_factor * 4),  # Cresce de 2 até ~12
        "border_width": round(0.8 + scale_factor * 0.6, 1)  # Cresce de 0.8 até ~2.2
    }
