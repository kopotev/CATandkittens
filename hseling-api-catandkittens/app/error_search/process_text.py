from error_search.highlighter import HTMLStyle
from error_search.search import Searcher


def process_text(tree):
    """
    Обработка входного текста - поиск ошибок
    :param text: входной текст (строка)
    :return: строка, где ошибочные слова окружены соответствующими html-тегами
    """
    if not tree:
        raise Exception("Empty tree")

    searcher = Searcher()
    if not searcher:
        raise Exception("Empty searcher")
    style = HTMLStyle()
    check = searcher.check_all(tree)
    out_t = []
    for s, sent in enumerate(tree): # TODO: делать это сразу в серчере, а то
        # TODO: обходим два раза одно и то же дерево как лохи
        for i, word in enumerate(sent):
            mistake = check.get((word['form'], s, i))
            if mistake:
                templ = '<span style="" >{}</span></html>'.format(word['form'])
                style_attr = ""
                for mis in mistake:
                    style_attr += style.color_scheme[mis]

                out_t.append(templ.replace('style=""', 'style="{}"'.format(style_attr)))

            else:
                out_t.append(word['form'])

    string = ' '.join(out_t)
    return string
