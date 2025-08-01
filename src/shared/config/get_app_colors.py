THEME_COLOR_NAMES = ['red', 'pink', 'purple', 'deeppurple', 'indigo', 'blue',
                     'cyan', 'teal', 'green', 'lime', 'yellow', 'amber',
                     'orange', 'deeporange', 'brown', 'grey',]

COLOR_DISPLAY_NAMES = {
    'red': 'Red',
    'pink': 'Pink',
    'purple': 'Purple',
    'deeppurple': 'Deep Purple',
    'indigo': 'Indigo',
    'blue': 'Blue',
    'cyan': 'Cyan',
    'teal': 'Teal',
    'green': 'Green',
    'lime': 'Lime',
    'yellow': 'Yellow',
    'amber': 'Amber',
    'orange': 'Orange',
    'deeporange': 'Deep Orange',
    'brown': 'Brown',
    'grey': 'Grey',
}

def get_theme_colors(color_name: str = 'blue') -> dict[str, str]:
    app_colors = {
        'red': {'base_color': 'red','primary': '#F44336', 'container': '#EF9A9A', 'accent': '#FF5252', 'appbar': '#D32F2F', 'background': '#260A08'},
        'pink': {'base_color': 'pink','primary': '#E91E63', 'container': '#F48FB1', 'accent': '#FF4081', 'appbar': '#C2185B', 'background': '#250A1B'},
        'purple': {'base_color': 'purple','primary': '#9C27B0', 'container': '#CE93D8', 'accent': '#E040FB', 'appbar': '#7B1FA2', 'background': '#17043E'},
        'deeppurple': {'base_color': 'deeppurple','primary': '#673AB7', 'container': '#B39DDB', 'accent': '#7C4DFF', 'appbar': '#512DA8', 'background': '#0A0632'},
        'indigo': {'base_color': 'indigo','primary': '#3F51B5', 'container': '#9FA8DA', 'accent': '#536DFE', 'appbar': '#303F9F', 'background': '#08103C'},
        'blue': {'base_color': 'blue','primary': '#2196F3', 'container': '#90CAF9', 'accent': '#448AFF', 'appbar': '#1976D2', 'background': '#051629'},
        'lightblue': {'base_color': 'lightblue','primary': '#03A9F4', 'container': '#81D4FA', 'accent': '#40C4FF', 'appbar': '#0288D1', 'background': '#051B26'},
        'cyan': {'base_color': 'cyan','primary': '#00BCD4', 'container': '#80DEEA', 'accent': '#4DD0E1', 'appbar': '#0097A7', 'background': '#041C20'},
        'teal': {'base_color': 'teal','primary': '#009688', 'container': '#80CBC4', 'accent': '#1DE9B6', 'appbar': '#00796B', 'background': '#001315'},
        'green': {'base_color': 'green','primary': '#4CAF50', 'container': '#A5D6A7', 'accent': '#69F0AE', 'appbar': '#388E3C', 'background': '#0A1B0B'},
        'lightgreen': {'base_color': 'lightgreen','primary': '#8BC34A', 'container': '#C5E1A5', 'accent': '#E6EE9C', 'appbar': '#7CB342', 'background': '#1C2908'},
        'lime': {'base_color': 'lime','primary': '#CDDC39', 'container': '#E6EE9C', 'accent': '#F0F4C3', 'appbar': '#C0CA33', 'background': '#243007'},
        'yellow': {'base_color': 'yellow','primary': '#FFEB3B', 'container': '#FFF59D', 'accent': '#FFD740', 'appbar': '#FBC02D', 'background': '#261E07'},
        'amber': {'base_color': 'amber','primary': '#FFC107', 'container': '#FFE082', 'accent': '#FFD54F', 'appbar': '#E6A200', 'background': '#261A04'},
        'orange': {'base_color': 'orange','primary': '#FF9800', 'container': '#FFCC80', 'accent': '#FFAB40', 'appbar': '#F57C00', 'background': '#261400'},
        'deeporange': {'base_color': 'deeporange','primary': '#FF5722', 'container': '#FFAB91', 'accent': '#FF6E40', 'appbar': '#E64A19', 'background': '#260F09'},
        'brown': {'base_color': 'brown','primary': '#795548', 'container': '#BCAAA4', 'accent': '#D7CCC8', 'appbar': '#6D4C41', 'background': '#130B08'},
        'grey': {'base_color': 'grey','primary': '#9E9E9E', 'container': '#EEEEEE', 'accent': '#E0E0E0', 'appbar': '#757575', 'background': '#1D1D1D'},
        'bluegrey': {'base_color': 'bluegrey','primary': '#607D8B', 'container': '#B0BEC5', 'accent': '#CFD8DC', 'appbar': '#455A64', 'background': '#10181C'},
    }

    return app_colors.get(color_name, app_colors['blue'])
