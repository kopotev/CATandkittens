from flask import Flask, jsonify, request
import logging

import boilerplate
import json
from hseling_api_catandkittens.process import *
from hseling_api_catandkittens.query import query_data



ALLOWED_EXTENSIONS = ['txt', 'conll', 'xlsx','udpipe','npy','w2v']

log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL=boilerplate.CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND=boilerplate.CELERY_RESULT_BACKEND
)
celery = boilerplate.make_celery(app)


@celery.task
def process_task(file_ids_list=None):
    files_to_process = boilerplate.list_files(recursive=True,
                                              prefix=boilerplate.UPLOAD_PREFIX)
    if file_ids_list:
        files_to_process = [boilerplate.UPLOAD_PREFIX + file_id
                            for file_id in file_ids_list
                            if (boilerplate.UPLOAD_PREFIX + file_id)
                            in files_to_process]
    data_to_process = {file_id[len(boilerplate.UPLOAD_PREFIX):]:
                           boilerplate.get_file(file_id)
                       for file_id in files_to_process}

    process_data(data_to_process)
    processed_file_ids = list()
    # for processed_file_id, contents in process_data(data_to_process):
    #     processed_file_ids.append(
    #         boilerplate.add_processed_file(
    #             processed_file_id,
    #             contents,
    #             extension='txt'
    #         ))
    return processed_file_ids

@celery.task(time_limit=1200,soft_time_limit=1200)
def process_user_text_task(input_text=''):
    if input_text:
        from conllu import parse
        from ufal.udpipe import Model, Pipeline
        from error_search.process_text import process_text
        import os
        udpipe_local_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),'error_search/russian-syntagrus-ud-2.0-170801.udpipe')
        if not os.path.exists(udpipe_local_path):
            boilerplate.fget_file('upload/russian-syntagrus-ud-2.0-170801.udpipe',udpipe_local_path)
        ud_model = Model.load(udpipe_local_path)
        pipeline = Pipeline(ud_model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
        out = pipeline.process(input_text)
        tree = parse(out)

        return process_text(tree)

@app.route('/upload', methods=['GET', 'POST'])
def upload_endpoint():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": boilerplate.ERROR_NO_FILE_PART})
        upload_file = request.files['file']
        if upload_file.filename == '':
            return jsonify({"error": boilerplate.ERROR_NO_SELECTED_FILE})
        if upload_file and boilerplate.allowed_file(
                upload_file.filename,
                allowed_extensions=ALLOWED_EXTENSIONS):
            return jsonify(boilerplate.save_file(upload_file))
    return boilerplate.get_upload_form()


@app.route('/files/<path:file_id>')
def get_file_endpoint(file_id):
    if file_id in boilerplate.list_files(recursive=True):
        return boilerplate.get_file(file_id)
    return jsonify({'error': boilerplate.ERROR_NO_SUCH_FILE})


@app.route('/files')
def list_files_endpoint():
    return jsonify({'file_ids': boilerplate.list_files(recursive=True)})


@app.route('/process')
@app.route("/process/<file_ids>")
def process_endpoint(file_ids=None):
    file_ids_list = file_ids and file_ids.split(",")
    task = process_task.delay(file_ids_list)
    return jsonify({"task_id": str(task)})


@app.route("/query/<path:file_id>")
def query_endpoint(file_id):
    query_type = request.args.get('type')
    if not query_type:
        return jsonify({"error": boilerplate.ERROR_NO_QUERY_TYPE_SPECIFIED})
    processed_file_id = boilerplate.PROCESSED_PREFIX + file_id
    if processed_file_id in boilerplate.list_files(recursive=True):
        return jsonify({"result": query_data({
            processed_file_id: boilerplate.get_file(processed_file_id)
        }, query_type=query_type)})
    return jsonify({"error": boilerplate.ERROR_NO_SUCH_FILE})


@app.route("/status/<task_id>")
def status_endpoint(task_id):
    return jsonify(boilerplate.get_task_status(task_id))


@app.route("/test_mysql")
def test_mysql_endpoint():
    conn = boilerplate.get_mysql_connection()
    cur = conn.cursor()
    cur.execute("SELECT table_name, column_name FROM INFORMATION_SCHEMA.COLUMNS")
    schema = dict()
    for table_name, column_name in cur.fetchall():
        schema.setdefault(table_name.decode('utf-8'), []).append(column_name)
    return jsonify({"schema": schema})


@app.route("/input_text", methods=['GET', 'POST'])
def process_input_text():
    got = request.get_json()
    if not got:
        raise Exception("Empty request: {0}".format(got))
    if isinstance(got, str):
        loaded = json.loads(got)
        if not loaded:
            raise Exception("Cannot load json")
    elif isinstance(got, dict):
        loaded = got
    input_text = loaded['text']
    task_id = process_user_text_task.delay(input_text)
    return jsonify({"input_text": str(task_id)})


@app.route("/search_text", methods=['GET', 'POST'])
def process_search_text():
    got, loaded = request.get_json(), None
    if isinstance(got, str):
        loaded = json.loads(got)
        if not loaded:
            raise Exception("Cannot load json")
    elif isinstance(got, dict):
        loaded = got
    if loaded.get('lemma1'):
        return jsonify({"found": search_data(loaded)})
    else:
        return jsonify({"found": search_data(loaded['text'])})


@app.route("/search_collocations", methods=['GET', 'POST'])
def process_search_collocations():
    got = request.get_json()
    if isinstance(got, str):
        loaded = json.loads(got)
        if not loaded:
            raise Exception("Cannot load json")
    elif isinstance(got, dict):
        loaded = got
    return jsonify({"found": search_collocations(loaded)})


@app.route("/search_metadata", methods=['GET', 'POST'])
def process_search_metadata():
    got = request.get_json()
    if isinstance(got, str):
        loaded = json.loads(got)
        if not loaded:
            raise Exception("Cannot load json")
    elif isinstance(got, dict):
        loaded = got
    return jsonify({"found": search_metadata(loaded['text'])})


def get_endpoints(ctx):
    def endpoint(name, description, active=True):
        return {
            "name": name,
            "description": description,
            "active": active
        }

    all_endpoints = [
        endpoint("root", boilerplate.ENDPOINT_ROOT),
        endpoint("scrap", boilerplate.ENDPOINT_SCRAP,
                 not ctx["restricted_mode"]),
        endpoint("upload", boilerplate.ENDPOINT_UPLOAD),
        endpoint("process", boilerplate.ENDPOINT_PROCESS),
        endpoint("query", boilerplate.ENDPOINT_QUERY),
        endpoint("status", boilerplate.ENDPOINT_STATUS),
        endpoint("input_text", boilerplate.ENDPOINT_INPUT)
    ]

    return {ep["name"]: ep for ep in all_endpoints if ep}


@app.route("/")
def main_endpoint():
    ctx = {"restricted_mode": boilerplate.RESTRICTED_MODE}
    return jsonify({"endpoints": get_endpoints(ctx)})


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)

__all__ = [app, celery]
