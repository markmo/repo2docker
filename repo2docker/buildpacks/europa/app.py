import logging
import subprocess
import os

from flask import abort, Flask, jsonify, request

app = Flask(__name__)


@app.route('/_ok')
def healthcheck():
    return 'ok'


@app.route('/autocommit')
def autocommit():
    os.chdir('/home/jovyan')
    subprocess.call(['./autocommit.sh'])


@app.route('/merge', methods=['POST'])
def merge():
    data = request.json()
    commit_message = data['commit_message']
    os.chdir('/home/jovyan')
    subprocess.call(['./merge.sh', '"{}"'.format(commit_message)])
