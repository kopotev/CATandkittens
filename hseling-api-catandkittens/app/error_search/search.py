from collections import defaultdict
import logging
from gensim.models import Word2Vec
import os
from boilerplate import fget_file


class Searcher:
    """
    Поиск ошибок. Переработан так, чтобы удобнее было перезаписывать текст с найденными ошибками для вывода пользователю
    """

    def __init__(self):
        self.found = defaultdict(list)
        self.flag_i_vs_we = ''
        self.found_word = defaultdict(list)

    def find_genitives(self, gen_chain, word, s, i, threshold=6):
        if word['feats'] and word['feats'].get('Case') == 'Gen':
            gen_chain.append((word['form'], s, i))
        else:
            if len(gen_chain) >= int(threshold):
                self.found['genitives'].append(gen_chain)
                for gen in gen_chain:
                    self.found_word[gen].append('genitives')
            gen_chain = []
        return gen_chain

    def find_wrong_comparativ(self, sent, word, i, s):
        if i + 1 < len(sent):
            next = sent[i + 1]
            if word['feats'] and next['feats'] and word['feats'].get('Degree') and next['feats'].get('Degree'):
                if word['feats']['Degree'] == 'Cmp' and next['feats']['Degree'] == 'Cmp':
                    self.found['comparatives'].append((word['form'], next['form'], s, i))
                    self.found_word[(word['form'], s, i)].append('comparativ')
                    self.found_word[(next['form'], s, i + 1)].append('comparativ')

    def find_wrong_coordinate_NPs(self, sent, i, s, word, model):
        if word['deprel'] and word['deprel'] == 'cc':
            head_position = int(word['head']) - 1
            if head_position < len(sent):
                head = sent[head_position]
                head_form = head['form']
                head_of_head_position = int(head['head']) - 1
                if head_of_head_position < len(sent):
                    head_of_head_form = sent[head_of_head_position]['form']

                    if head_of_head_form:
                        if head_form in model.wv.vocab and head_of_head_form in model.wv.vocab:
                            sim = model.wv.similarity(head_form, head_of_head_form)
                        else:
                            sim = float('-inf')
                        if sim < -0.05:  # порог получен из "шел дождь и рота солдат"
                            self.found_word[(head_form, s, head_position)].append('coordinate_NPs')
                            self.found_word[(word['form'], s, i)].append('coordinate_NPs')
                            self.found_word[(head_of_head_form, s, head_of_head_position)].append('coordinate_NPs')

    def not_in_vocabulary(self, word, i, model, s):
        if word['upostag'] in ['NOUN', 'ADJ', 'VERB', 'ADV'] and word['form'].lower() not in model.wv.vocab:
            self.found['not in vocabulary'].append((word['form'], s, i))
            self.found_word[(word['form'], s, i)].append('not in vocabulary')

    def i_vs_we(self, i, word, s):
        if word['lemma'].lower() == 'я' and not self.flag_i_vs_we:
            self.flag_i_vs_we = 'i'
            self.found['i vs we'].append((word['form'], s, i))
            self.found_word[(word['form'], s, i)].append('i vs we')
        elif (word['lemma'].lower() == 'я' and self.flag_i_vs_we == 'we') or (
                word['lemma'].lower() == 'мы' and self.flag_i_vs_we == 'i'):
            self.found['i vs we'].append((word['form'], s, i))
            self.found_word[(word['form'], s, i)].append('i vs we')
        elif word['lemma'].lower() == 'мы' and not self.flag_i_vs_we:
            self.flag_i_vs_we = 'we'
            self.found['i vs we'].append((word['form'], s, i))
            self.found_word[(word['form'], s, i)].append('i vs we')

    def check_mood(self, sent, i, word, s):
        if word['form'] == 'бы' and i > 0:
            self.found['subjunctive mood'].append((sent[i - 1]['form'], word['form'], s, i))
            self.found_word[(sent[i - 1]['form'], s, i - 1)].append('subjunctive mood')
            self.found_word[(word['form'], s, i)].append('subjunctive mood')
        if word['feats'] and 'Mood' in word['feats'].keys() and word['feats']['Mood'] == 'Imp':
            self.found['imperative mood'].append((word['form'], s, i))
            self.found_word[(word['form'], s, i)].append('imperative mood')

    def check_all(self, tree):
        # s - sentence number
        # i - word number
        local_w2v_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'models')
        if not os.path.exists(local_w2v_path):
            os.mkdir(local_w2v_path)
        local_w2v_model_path = os.path.join(local_w2v_path, 'LinguisticModel')
        if not os.path.exists(local_w2v_model_path):
            fget_file('upload/LinguisticModel.w2v.trainables.syn1neg.npy',
                      os.path.join(local_w2v_path, 'LinguisticModel.trainables.syn1neg.npy'))
            fget_file('upload/LinguisticModel.w2v.wv.vectors.npy',
                      os.path.join(local_w2v_path, 'LinguisticModel.wv.vectors.npy'))
            fget_file('upload/LinguisticModel.w2v', local_w2v_model_path)
        try:
            model = Word2Vec.load(local_w2v_model_path)
        except FileNotFoundError:
            raise Exception("w2v model not found, current directory is {0}".format(os.getcwd()))
        logging.basicConfig(level=logging.INFO, filename='found.log')
        for s, sent in enumerate(tree):
            gen_chain = []

            for i, word in enumerate(sent):
                self.check_mood(sent, i, word, s)
                self.i_vs_we(i, word, s)
                self.not_in_vocabulary(word, i, model, s)
                gen_chain = self.find_genitives(gen_chain, word, s, i)
                self.find_wrong_comparativ(sent, word, i, s)
                self.find_wrong_coordinate_NPs(sent, i, s, word, model)

        for key, value in self.found.items():
            logging.info(key)
            for mistake in value:
                logging.info(mistake)

        return self.found_word
