import json
import logging
import subprocess
import os
import sys
import urllib.parse

from flask import abort, Flask, jsonify, request, Response
from flask_cors import CORS, cross_origin
from logging.config import dictConfig
from threading import Thread

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def root():
    return 'ok'


@app.route('/_ok')
def healthcheck():
    return 'ok'


## TODO is POST supported by jupyter-server-proxy

# @app.route('/autocommit', methods=['POST'])
# def autocommit():
#     os.chdir('/home/jovyan')
#     subprocess.call(['./autocommit.sh'])
#     return 'ok'


# @app.route('/merge', methods=['POST'])
# def merge():
#     data = request.json()
#     commit_message = data['commit_message']
#     app.logger.info('/merge called with commit message: %s', commit_message)
#     subprocess.Popen(['/bin/bash', '-i', '-c', '/home/jovyan/merge.sh', '"{}"'.format(commit_message)],
#         cwd='/home/jovyan',
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE
#     )
#     return 'ok'
@app.route('/merge', methods=['GET'])
def merge():
    commit_message = urllib.parse.unquote(request.args.get('commit_message'))
    app.logger.info('/merge called with commit message: %s', commit_message)
    subprocess.Popen(['sudo', '-i', '-u', 'jovyan', 'merge.sh', commit_message],
        cwd='/home/jovyan',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return 'ok'


has_garden_started = False
messages = []
has_garden_deleted = False


@app.route('/garden-status', methods=['GET'])
@cross_origin()
def garden_status():
    return jsonify({
        'ready': has_garden_started,
        'messages': messages
    })


@app.route('/garden-delete-status', methods=['GET'])
@cross_origin()
def garden_delete_status():
    return jsonify({
        'ready': has_garden_deleted,
        'messages': messages
    })


@app.route('/delete-garden', methods=['GET'])
@cross_origin
def delete_garden():
    app.logger.info('/delete-garden called')
    repo_name = urllib.parse.unquote(request.args.get('repo_name'))
    os.environ['REPO_NAME'] = repo_name;
    p = subprocess.Popen(['/root/.garden/bin/garden', 'delete', 'environment', '--logger-type=json'],
        cwd='/home/jovyan/work',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    global has_garden_deleted
    global messages
    has_garden_deleted = False
    messages = []

    def do_work():
        global has_garden_deleted
        while p.poll() is None:
            try:
                line = p.stdout.readline()
                line = line.decode(sys.stdout.encoding).strip('\x00')
                app.logger.debug(line)
                r = json.loads(line)
                messages.append(r)
                if r['msg'] == 'Deleting namespaces':
                    has_garden_deleted = True
                    break
            except:
                app.logger.error('Unexpected error: %s', sys.exc_info()[0])

    thread = Thread(target=do_work)
    thread.start()
    return 'ok'


# method must be GET when using SSE
@app.route('/stop-garden', methods=['GET'])
@cross_origin()
def stop_garden():
    app.logger.info('/stop-garden called')
    repo_name = urllib.parse.unquote(request.args.get('repo_name'))
    os.environ['REPO_NAME'] = repo_name;
    p = subprocess.Popen(['/root/.garden/bin/garden', 'delete', 'environment', '--logger-type=json'],
        cwd='/home/jovyan/work',
        # have it covered in supervisord config, otherwise need this
        # for garden/kubectl to find the kube config
        # env={
        #     'USER': 'root',
        #     'HOME': '/root',
        #     'KUBECONFIG': '/root/.kube/config'
        # }
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    global has_garden_deleted
    global messages
    has_garden_deleted = False
    messages = []

    def do_delete():
        global has_garden_deleted
        while p.poll() is None:
            try:
                line = p.stdout.readline()
                line = line.decode(sys.stdout.encoding).strip('\x00')
                app.logger.debug(line)
                r = json.loads(line)
                messages.append(r)
                msg = r.get('msg', None)
                if msg is not None:
                    m = msg.lower()
                    if 'aborting' in m:
                        # raise Exception('No enabled modules found in project.')
                        raise Exception(messages[-2])
                    elif 'deleting namespaces' in m:
                        has_garden_deleted = True
                        break
            except:
                app.logger.error('Unexpected error: %s', sys.exc_info()[0])

    thread = Thread(target=do_delete)
    thread.start()
    return 'ok'


# method must be GET when using SSE
@app.route('/start-garden', methods=['GET'])
@cross_origin()
def start_garden():
    app.logger.info('/start-garden called')
    repo_name = urllib.parse.unquote(request.args.get('repo_name'))
    os.environ['REPO_NAME'] = repo_name;
    p = subprocess.Popen(['/root/.garden/bin/garden', 'dev', '--logger-type=json'],
        cwd='/home/jovyan/work',
        # have it covered in supervisord config, otherwise need this
        # for garden/kubectl to find the kube config
        # env={
        #     'USER': 'root',
        #     'HOME': '/root',
        #     'KUBECONFIG': '/root/.kube/config'
        # }
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    global has_garden_started
    global messages
    has_garden_started = False
    messages = []

    def do_work():
        global has_garden_started
        while p.poll() is None:
            try:
                line = p.stdout.readline()
                line = line.decode(sys.stdout.encoding).strip('\x00')
                app.logger.debug(line)
                r = json.loads(line)
                messages.append(r)
                msg = r.get('msg', None)
                if msg is not None:
                    m = msg.lower()
                    if 'aborting' in m:
                        # raise Exception('No enabled modules found in project.')
                        raise Exception(messages[-2])
                    elif 'waiting for code changes' in m:
                        has_garden_started = True
                        break
            except:
                app.logger.error('Unexpected error: %s', sys.exc_info()[0])

    thread = Thread(target=do_work)
    thread.start()
    return 'ok'

    # TODO
    # def event_stream():
    #     while p.poll() is None:
    #         line = p.stdout.readline()
    #         line = line.decode(sys.stdout.encoding).strip('\x00')
    #         app.logger.debug(line)
    #         yield 'data: {}\n\n'.format(line)

    # return Response(event_stream(), mimetype='text/event-stream', headers={
    #     'Content-Type': 'text/event-stream',
    #     'Cache-Control': 'no-cache',
    #     'X-Accel-Buffering': 'no'
    # })
