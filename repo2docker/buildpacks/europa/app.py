import logging
import subprocess
import os
import sys

from flask import abort, Flask, jsonify, request, Response
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


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


@app.route('/start-garden', methods=['GET'])
@cross_origin()
def start_garden():
    p = subprocess.Popen(['garden', 'dev', '--logger-type=json'],
        cwd='/home/jovyan/work',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    def event_stream():
        while p.poll() is None:
            line = p.stdout.readline()
            yield 'data: {}\n\n'.format(line.decode(sys.stdout.encoding).strip('\x00'))

    return Response(event_stream(), mimetype='text/event-stream')
