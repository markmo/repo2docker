import json
import logging
import subprocess
import os
import sys

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
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def root():
    return 'ok'


@app.route('/_ok')
def healthcheck():
    return 'ok'


@app.route('/autocommit', methods=['POST'])
def autocommit():
    os.chdir('/home/jovyan')
    subprocess.call(['./autocommit.sh'])
    return 'ok'


@app.route('/merge', methods=['POST'])
def merge():
    data = request.json()
    commit_message = data['commit_message']
    os.chdir('/home/jovyan')
    subprocess.call(['./merge.sh', '"{}"'.format(commit_message)])
    return 'ok'


has_garden_started = False
messages = []


@app.route('/garden-status', methods=['GET'])
@cross_origin()
def garden_status():
    return jsonify({
        'ready': has_garden_started,
        'messages': messages
    })


@app.route('/start-garden', methods=['GET'])
@cross_origin()
def start_garden():
    app.logger.info('/start-garden called')
    p = subprocess.Popen(['garden', 'dev', '--logger-type=json'],
        cwd='/home/jovyan/work',
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
            line = p.stdout.readline()
            line = line.decode(sys.stdout.encoding).strip('\x00')
            app.logger.debug(line)
            r = json.loads(line)
            messages.append(r)
            if r['msg'] == 'Waiting for code changes...':
                has_garden_started = True
                break

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
