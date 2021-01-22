from boilerplate import get_mysql_connection
import defusedxml
from defusedxml.common import EntitiesForbidden
from xlrd import open_workbook
from tqdm import tqdm

defusedxml.defuse_stdlib()
CON = get_mysql_connection()
CUR = CON.cursor(dictionary=True)
COLLOCATION_TABLES_MAPPING = {'Лингвистика': 'linguistics',
                              'Социология': 'sociology',
                              'Политология': 'politology',
                              'Юриспруденция': 'law',
                              'Психология и педагогика': 'psychology',
                              'Экономика': 'economics'}


def write_to_db_metas(data_to_process):
    """
    Upload metadata
    """
    CUR.execute("SHOW TABLES")
    result = CUR.fetchall()
    tables = [list(dictionary.values())[0].decode("utf-8") for dictionary in result]
    if 'meta_cat' not in tables:
        create_table_metas = "CREATE TABLE IF NOT EXISTS meta_cat (id_text INT AUTO_INCREMENT, domain VARCHAR(255), year INT, author VARCHAR(255), journal VARCHAR(255), source VARCHAR(255), article_name VARCHAR(255), PRIMARY KEY (id_text))"
        CUR.execute(create_table_metas)

    for text in data_to_process.values():
        text = text.decode("utf-8")
        text = text.replace("'", "\\'")
        lines = text.splitlines()
        metadata = []
        for line in lines:
            if line != '':
                metadata.append(line)
        CUR.execute(
            "INSERT INTO meta_cat (domain, year, author, journal, source, article_name) VALUES (%s, %s, %s, %s, %s, %s)",
            (metadata[4], metadata[3], metadata[2], metadata[5], metadata[0], metadata[1]))
        CON.commit()
        # чтобы получить в поиске вновь добавленные данные, api придется пересобрать


def write_to_db_words(data_to_process):
    """
    Upload info from conll files
    """
    CUR.execute("SHOW TABLES")
    result = CUR.fetchall()
    tables = [list(dictionary.values())[0].decode("utf-8") for dictionary in result]
    if 'words_cat' not in tables:
        create_table_words = "CREATE TABLE IF NOT EXISTS words_cat (id_word INT AUTO_INCREMENT, abs_sent_id INT, id_sent INT, id_text INT, word VARCHAR(255), lemma VARCHAR(255), POS_tag VARCHAR(255), morph VARCHAR(255), root_dist INT, sint_role VARCHAR(255), PRIMARY KEY (id_word), FOREIGN KEY foreign_key_id_text(id_text) REFERENCES meta_cat(id_text) ON UPDATE CASCADE ON DELETE CASCADE)"
        CUR.execute(create_table_words)
    get_last_metas = "SELECT MAX(id_text) FROM meta_cat"
    CUR.execute(get_last_metas)
    idtext = CUR.fetchall()[0]['MAX(id_text)']
    for file in data_to_process.values():
        text = file.decode("utf-8")
        text = text.replace("'", "\\'")
        lines = text.splitlines()
        abs_sent_id = 1  # к какому по счету предложению в тексте относится слово
        for line in lines:
            if line != '':
                if line[0] != '#':  # в формате udpipe номер предложения и текст закоменчены #
                    spl_line = line.split('\t')
                    CUR.execute(
                        "INSERT INTO words_cat (id_text, abs_sent_id, id_sent, word, lemma, POS_tag, morph, root_dist, sint_role) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (idtext, abs_sent_id, spl_line[0], spl_line[1], spl_line[2], spl_line[3], spl_line[5],
                         spl_line[6], spl_line[7]))
                    CON.commit()
            else:
                abs_sent_id += 1


def write_to_db_collocations(data_to_process):
    domain = list(data_to_process.keys())[0].split('.')[0]
    for i in range(2, 7):
        tablename = "collocations_{0}_grams_{1}".format(i, domain)
        CUR.execute("SHOW TABLES")
        result = CUR.fetchall()
        tables = [list(dictionary.values())[0].decode("utf-8") for dictionary in result]
        if tablename not in tables:
            create_table = "CREATE TABLE IF NOT EXISTS " + tablename + " (id_collocation INT AUTO_INCREMENT, occurence VARCHAR(255), lemma VARCHAR(255), POS_tag VARCHAR(255), absolute_frequency FLOAT, normalized_frequency FLOAT, PMI FLOAT, log_likelihood FLOAT, t_score FLOAT, PRIMARY KEY (id_collocation))"
            CUR.execute(create_table)
    for file in data_to_process.values():
        try:
            data = open_workbook(file_contents=file)
            for i, sheetname in enumerate(tqdm(('bigrams', 'trigrams', 'quadrograms', 'fivegrams', 'sixgrams'))):
                ngrams = data.sheet_by_name(sheetname)
                for r in range(1, ngrams.nrows):
                    occurence = ngrams.cell(r, 3).value
                    pos = ngrams.cell(r, 7).value
                    abs_freq = ngrams.cell(r, 1).value
                    norm_freq = ngrams.cell(r, 5).value
                    pmi = ngrams.cell(r, 4).value
                    log_like = ngrams.cell(r, 2).value
                    t_score = ngrams.cell(r, 6).value
                    values = (occurence, pos, abs_freq, norm_freq, pmi, log_like, t_score)
                    CUR.execute("INSERT INTO " + "collocations_{0}_grams_{1}".format(
                        i + 2,
                        domain) + " (occurence, POS_tag, absolute_frequency, normalized_frequency, PMI, log_likelihood, t_score) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                values)
                CON.commit()
        except EntitiesForbidden:
            raise ValueError('Please use a xlsx file without XEE')


def search_in_db(data_to_search):
    if isinstance(data_to_search, dict):
        query = "SELECT id_word, id_text, abs_sent_id, word, lemma FROM words_cat WHERE (id_text, abs_sent_id) IN (SELECT id_text, abs_sent_id FROM words_cat WHERE lemma = %s "
        params = [data_to_search['lemma1']]
        if data_to_search["search-domain"] != 'Предметная область':
            query = "SELECT id_word, id_text, abs_sent_id, word, lemma FROM words_cat WHERE (id_text, abs_sent_id) IN (SELECT words_cat.id_text, words_cat.abs_sent_id FROM words_cat INNER JOIN meta_cat ON words_cat.id_text = meta_cat.id_text WHERE words_cat.lemma = %s "
            domain = data_to_search['search-domain']
            query += "AND meta_cat.domain = %s "
            params.append(domain)
        if data_to_search.get('morph1'):
            morphs = data_to_search['morph1'].split(',')
            for morph in morphs:
                if morph.isupper():
                    query += "AND POS_tag = %s "
                    params.append(morph)
                else:
                    query += "AND morph LIKE %s "
                    params.append('%' + morph + '%')
        if data_to_search.get("syntax") != "Синтаксическое отношение":
            syntax = data_to_search['syntax'].split(':')[0]
            query += "AND sint_role = %s "
            params.append(syntax)
        CUR.execute(query.rstrip() + ")", tuple(params))
        fetched = CUR.fetchall()
        if not data_to_search.get('lemma2'):
            return fetched
        elif data_to_search.get('lemma1') and data_to_search.get('lemma2'):
            first_lemmas_ids = [f['id_word'] for f in fetched if f['lemma'] == data_to_search['lemma1']]
            min_dist, max_dist, syntax, morph2 = -1, 1, None, None
            if data_to_search.get("min"):
                min_dist = data_to_search['min']
            if data_to_search.get("max"):
                max_dist = data_to_search['max']

            right_dist_ids = []

            for id in first_lemmas_ids:
                lowest, highest = int(id) + min_dist, int(id) + max_dist
                second_lemma_query, second_lemma_params = "SELECT id_word FROM words_cat WHERE lemma = %s AND id_word BETWEEN  %s AND  %s ", \
                                                          [data_to_search['lemma2'], lowest, highest]
                if data_to_search.get("morph2"):
                    morphs2 = data_to_search['morph2'].split(',')
                    for morph in morphs2:
                        if morph.isupper():
                            second_lemma_query += "AND POS_tag = %s "
                            second_lemma_params.append(morph)
                        else:
                            second_lemma_query += "AND morph LIKE %s "
                            second_lemma_params.append('%' + morph + '%')
                if data_to_search.get("syntax") != "Синтаксическое отношение":
                    second_lemma_query += "AND id_sent = (SELECT root_dist FROM words_cat WHERE id_word = %s) "
                    second_lemma_params.append(id)
                CUR.execute(second_lemma_query.rstrip(), tuple(second_lemma_params))
                found = CUR.fetchall()
                if found:  # всё дальше имеет смысл, только если вторая лемма нашлась с заданными параметрами
                    right_dist_ids.append(id)

            if right_dist_ids:
                instring = '(' + ','.join(map(str, right_dist_ids)) + ')'
                query = "SELECT id_word, id_text, abs_sent_id, word, lemma FROM words_cat WHERE (id_text, abs_sent_id) IN (SELECT id_text, abs_sent_id FROM words_cat WHERE id_word IN " + instring + ")"
                CUR.execute(query)
                return CUR.fetchall()
            else:
                return dict()

        else:
            return dict()
    else:
        CUR.execute(
            "SELECT id_word, id_text, abs_sent_id, word FROM words_cat WHERE (id_text, abs_sent_id) IN (SELECT id_text, abs_sent_id FROM words_cat WHERE word = %s)",
            (data_to_search,))
    return CUR.fetchall()


def search_in_collocations(data_to_search):
    param = '%' + data_to_search['text'] + '%'
    if not data_to_search.get('count'):
        query = "SELECT * FROM collocations_2_grams WHERE occurence LIKE %s"
        if data_to_search.get('domain'):
            query = "SELECT * FROM collocations_2_grams_{0} WHERE occurence LIKE %s".format(
                COLLOCATION_TABLES_MAPPING[data_to_search['domain']])
    elif data_to_search.get('count'):
        query = "SELECT * FROM collocations_{0}_grams ".format(data_to_search['count']) + "WHERE occurence LIKE %s"
        if data_to_search.get('domain'):
            query = "SELECT * FROM collocations_{0}_grams_{1} ".format(data_to_search['count'],
                                                                       COLLOCATION_TABLES_MAPPING[data_to_search[
                                                                           'domain']]) + "WHERE occurence LIKE %s"
        # count приходит не от юзера
    CUR.execute(query, (param,))
    return CUR.fetchall()


def search_in_metadata(data_to_search):
    CUR.execute("SELECT * FROM meta_cat WHERE id_text = %s", (data_to_search,))
    return CUR.fetchall()
