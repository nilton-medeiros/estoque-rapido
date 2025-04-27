def get_app_colors(color_name: str) -> dict:
    app_colors = {
        'deeppurple': {'base_color': 'deeppurple','primary': '#673AB7', 'container': '#B39DDB', 'accent': '#7C4DFF', 'appbar': '#512DA8'},
        'purple': {'base_color': 'purple','primary': '#9C27B0', 'container': '#CE93D8', 'accent': '#E040FB', 'appbar': '#7B1FA2'},
        'indigo': {'base_color': 'indigo','primary': '#3F51B5', 'container': '#9FA8DA', 'accent': '#536DFE', 'appbar': '#303F9F'},
        'blue': {'base_color': 'blue','primary': '#2196F3', 'container': '#90CAF9', 'accent': '#448AFF', 'appbar': '#1976D2'},
        'teal': {'base_color': 'teal','primary': '#009688', 'container': '#80CBC4', 'accent': '#1DE9B6', 'appbar': '#00796B'},
        'green': {'base_color': 'green','primary': '#4CAF50', 'container': '#A5D6A7', 'accent': '#69F0AE', 'appbar': '#388E3C'},
        'yellow': {'base_color': 'yellow','primary': '#FFEB3B', 'container': '#FFF59D', 'accent': '#FFD740', 'appbar': '#FBC02D'},
        'orange': {'base_color': 'orange','primary': '#FF9800', 'container': '#FFCC80', 'accent': '#FFAB40', 'appbar': '#F57C00'},
        'deeporange': {'base_color': 'deeporange','primary': '#FF5722', 'container': '#FFAB91', 'accent': '#FF6E40', 'appbar': '#E64A19'},
        'pink': {'base_color': 'pink','primary': '#E91E63', 'container': '#F48FB1', 'accent': '#FF4081', 'appbar': '#C2185B'},
        'red': {'base_color': 'red','primary': '#F44336', 'container': '#EF9A9A', 'accent': '#FF5252', 'appbar': '#D32F2F'},
    }

    return app_colors.get(color_name, {
        'base_color': 'yellow',
        'primary': '#FFEB3B',  # ft.Colors.YELLOW
        'container': '#FFF59D',  # ft.Colors.YELLOW_200
        'accent': '#FFD740',  # ft.Colors.YELLOW_ACCENT_400
        'appbar': '#FBC02D', # ft.Colors.YELLOW_700
    })
