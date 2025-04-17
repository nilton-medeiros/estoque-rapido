def get_app_colors(cor: str) -> dict:
    app_colors = {
        'deeppurple': {'base_color': 'deeppurple','primary': '#673AB7', 'container': '#B39DDB', 'accent': '#7C4DFF'},
        'purple': {'base_color': 'purple','primary': '#9C27B0', 'container': '#CE93D8', 'accent': '#E040FB'},
        'indigo': {'base_color': 'indigo','primary': '#3F51B5', 'container': '#9FA8DA', 'accent': '#536DFE'},
        'blue': {'base_color': 'blue','primary': '#2196F3', 'container': '#90CAF9', 'accent': '#448AFF'},
        'teal': {'base_color': 'teal','primary': '#009688', 'container': '#80CBC4', 'accent': '#1DE9B6'},
        'green': {'base_color': 'green','primary': '#4CAF50', 'container': '#A5D6A7', 'accent': '#69F0AE'},
        'yellow': {'base_color': 'yellow','primary': '#FFEB3B', 'container': '#FFF59D', 'accent': '#FFD740'},
        'orange': {'base_color': 'orange','primary': '#FF9800', 'container': '#FFCC80', 'accent': '#FFAB40'},
        'deeporange': {'base_color': 'deeporange','primary': '#FF5722', 'container': '#FFAB91', 'accent': '#FF6E40'},
        'pink': {'base_color': 'pink','primary': '#E91E63', 'container': '#F48FB1', 'accent': '#FF4081'},
        'red': {'base_color': 'red','primary': '#F44336', 'container': '#EF9A9A', 'accent': '#FF5252'},
    }

    return app_colors.get(cor, {
        'base_color': 'blue',
        'primary': '#2196F3',
        'container': '#90CAF9',
        'accent': '#448AFF'
    })
