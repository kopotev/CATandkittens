# здесь используется nltk, который на самом деле не нужен,
# потому что на слова и предложения делит udpipe

# мне в целом сомнительно, что readability будет использоваться,
# поэтому пока закоменчиваю, чтобы не падало на импорте неустановленной библиотеки

# import re
#
# from math import sqrt
#
# from nltk.tokenize import sent_tokenize
#
# Flesh_Kincaid_start = -7.819055689838727
# Flesh_Kincaid_end = 28.17120226515197
# Coleman_Liau_start = -5.83735309283683
# Coleman_Liau_end = 24.74512164858369
# SMOG_start = 9.855746639390741
# SMOG_end = 31.327702646088834
# Dale_Chale_start = 10.30222016501114
# Dale_Chale_end = 32.70239222865304
# ARI_start = -7.664234962894685
# ARI_end = 28.39406066625659
#
# def get_metrics(text):
#     '''
#     Получение разных индексов удобочитаемости и других метрик
#     :param text: исходный текст (строка)
#     :return: словарь с набором параметров
#     '''
#
#     FLG_X_GRADE = 0.318
#     FLG_Y_GRADE = 14.2
#     FLG_Z_GRADE = 30.5
#
#     CLI_X_GRADE = 0.055
#     CLI_Y_GRADE = 0.35
#     CLI_Z_GRADE = 20.33
#
#     SMOG_X_GRADE = 1.1
#     SMOG_Y_GRADE = 64.6
#     SMOG_Z_GRADE = 0.05
#
#     DC_X_GRADE = 0.552
#     DC_Y_GRADE = 0.273
#
#     ARI_X_GRADE = 6.26
#     ARI_Y_GRADE = 0.2805
#     ARI_Z_GRADE = 31.04
#
#     words = re.findall('\w+', text)
#     n_words = len(words)
#     n_unique_words = len(list(set(words)))
#     n_syllabes = len(re.findall('а|е|и|у|о|я|ё|э|ю|я|ы', text))
#     n_psyl = 0
#     n_letters = len(re.findall('а|е|и|у|о|я|ё|э|ю|я|ы|й|ц|к|н|г|ш|щ|з|х|ъ|ф|в|п|р|л|д|ж|ч|с|м|т|ь|б', text))
#     for word in words:
#         if len(re.findall('а|е|и|у|о|я|ё|э|ю|я|ы', word)) > 3:
#             n_psyl += 1
#     n_sent = len(sent_tokenize(text))
#
#     Flesh_Kincaid = 0
#     if n_words > 0 and n_sent > 0:
#         Flesh_Kincaid = FLG_X_GRADE * (float(n_words) / n_sent) + FLG_Y_GRADE * (float(n_syllabes) / n_words) - FLG_Z_GRADE
#     else:
#         pass
#
#     Coleman_Liau = 0
#     if n_words > 0:
#         Coleman_Liau = CLI_X_GRADE * (n_letters * (100.0 / n_words)) - CLI_Y_GRADE * (n_sent * (100.0 / n_words)) - CLI_Z_GRADE
#     else:
#         pass
#
#     SMOG = SMOG_X_GRADE * sqrt((float(SMOG_Y_GRADE) / n_sent) * n_psyl) + SMOG_Z_GRADE
#
#     Dale_Chale = DC_X_GRADE * (100.0 * n_psyl / n_words) + DC_Y_GRADE * (float(n_words) / n_sent)
#
#     ARI = 0
#     if n_words > 0 and n_sent > 0:
#         ARI = ARI_X_GRADE * (float(n_letters) / n_words) + ARI_Y_GRADE * (float(n_words) / n_sent) - ARI_Z_GRADE
#     else:
#         pass
#
#     TTR = n_unique_words / n_words
#
#     return {'n_words': n_words
#         , 'n_syllabes': n_syllabes
#         , 'n_letters': n_letters
#         , 'n_psyl': n_psyl
#         , 'n_sent': n_sent
#         , 'TTR': TTR
#         , 'Flesh_Kincaid': Flesh_Kincaid
#         , 'Coleman_Liau': Coleman_Liau
#         , "SMOG": SMOG
#         , 'Dale_Chale': Dale_Chale
#         , 'ARI': ARI}
#
#
# def check_text(text):
#     """
#     Проверка на удобочитаемость
#     :param text: входной текст
#     :return: пользовательский вывод: информация о тексте в виде строки
#     """
#     text_metrics = get_metrics(text)
#     count_too_much = 0
#     count_too_little = 0
#     average = str()
#     words = 'Число слов: {}'.format(text_metrics['n_words'])
#     sentences = 'Число предложений: {}'.format(text_metrics['n_sent'])
#     ttr = 'Type-token ratio: {}'.format(text_metrics['TTR'])
#     fki = 'Индекс Флеша-Кинкейда: {}'.format(text_metrics['Flesh_Kincaid'])
#     if text_metrics['Flesh_Kincaid']<Flesh_Kincaid_start:
#         count_too_little += 1
#     elif text_metrics['Flesh_Kincaid']>Flesh_Kincaid_end:
#         count_too_much += 1
#     cli = 'Индекс Колман-Лиау:  {}'.format(text_metrics['Coleman_Liau'])
#     if text_metrics['Coleman_Liau']<Coleman_Liau_start:
#         count_too_little += 1
#     elif text_metrics['Coleman_Liau']>Coleman_Liau_end:
#         count_too_much += 1
#     smog = 'Индекс SMOG: {}'.format(text_metrics['SMOG'])
#     if text_metrics['SMOG']<SMOG_start:
#         count_too_little += 1
#     elif text_metrics['SMOG']>SMOG_end:
#         count_too_much += 1
#     dci = 'Индекс Дейла-Чалл: {}'.format(text_metrics['Dale_Chale'])
#     if text_metrics['Dale_Chale']<Dale_Chale_start:
#         count_too_little += 1
#     elif text_metrics['Dale_Chale']>Dale_Chale_end:
#         count_too_much += 1
#     ari = 'Индекс ARI: {}'.format(text_metrics['ARI'])
#     if text_metrics['ARI']<ARI_start:
#         count_too_little += 1
#     elif text_metrics['ARI']>ARI_end:
#         count_too_much += 1
#
#     if count_too_little >= 3:
#         average += 'Удобочитаемость текста существенно ниже средней по корпусу'
#     if count_too_much >= 3:
#         average += 'Удобочитаемость текста существенно выше средней по корпусу'
#     else:
#         average += 'Удобочитаемость текста средняя'
#
#     conclusion = words + '\n' + sentences + '\n' + ttr + '\n' + fki + '\n' + cli + '\n' + smog + '\n' + dci + '\n' + ari + '\n' + average
#
#     return conclusion
