COLOR_SCHEME = {'genitives':  "background-color: SlateBlue;"
                , 'comparativ':"background-color: #66CDAA;"
                , 'coordinate_NPs': "background-color: #228B22;"
                , 'not in vocabulary': "font-weight:bold;color: Red;"
                , 'i vs we': "font-weight:bold;color: #8B008B;"
                , 'imperative mood': "background-color: DeepSkyBlue;"
                , 'subjunctive mood': "background-color: Violet;"}

class HTMLStyle:
    """
    Класс для создания цветовой схемы текста
    """
    def __init__(self, color_scheme=COLOR_SCHEME):
        self.color_scheme = color_scheme

