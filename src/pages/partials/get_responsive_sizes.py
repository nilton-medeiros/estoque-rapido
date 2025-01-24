

def get_responsive_sizes(page_width: int) -> dict:
    if page_width < 600:  # Mobile
        return {
            "font_size": 14,
            "icon_size": 16,
            "button_width": 200,
            "input_width": 280,
            "form_padding": 20,
            "spacing": 4,
            "border_width": 1.5
        }
    elif page_width < 1024:  # Tablet
        return {
            "font_size": 16,
            "icon_size": 20,
            "button_width": 250,
            "input_width": 350,
            "form_padding": 40,
            "spacing": 6,
            "border_width": 2
        }
    else:  # Desktop
        return {
            "font_size": 18,
            "icon_size": 24,
            "button_width": 300,
            "input_width": 400,
            "form_padding": 50,
            "spacing": 8,
            "border_width": 2.5
        }
