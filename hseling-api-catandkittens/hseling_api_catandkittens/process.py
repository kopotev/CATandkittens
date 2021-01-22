from work_with_db import *


def process_data(data_to_process):
    """add data to the database
    """
    for key in data_to_process.keys():
        if key[-3:] == 'txt':
            write_to_db_metas(data_to_process)
        elif key[-5:] == 'conll':
            write_to_db_words(data_to_process)
        elif key[-4:] == 'xlsx':
            write_to_db_collocations(data_to_process)
        elif key.rsplit('.', 1)[1].lower() in ['udpipe','npy','w2v']:
            pass
        else:
            raise Exception("Wrong filename: {0}".format(key))


def search_data(data_to_search):
    """
    search in the CAT tables
    :param data_to_search:
    :return: (dict)
    """
    return search_in_db(data_to_search)


def search_collocations(data_to_search):
    """
    search in the collocations dictionary tables
    :param data_to_search:
    :return: (dict)
    """
    return search_in_collocations(data_to_search)

def search_metadata(data_to_search):
    """
    search in the metadata by text id
    :param data_to_search:
    :return: (dict)
    """
    return search_in_metadata(data_to_search)
