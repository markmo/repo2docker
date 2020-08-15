# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from jupyter_core.paths import jupyter_data_dir
import subprocess
import os
import errno
import stat
import sys

c = get_config()
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.allow_origin = '*'
# Cache-Control - prevent https://github.com/nteract/nteract/issues/3850
c.NotebookApp.tornado_settings = {
  'cookie_options': {
    'samesite': 'none'
  },
  'headers': {
    'Content-Security-Policy': "frame-ancestors 'self' https://*.atlassian.net https://bitbucket.org https://*.bitbucket.org https://*.ngrok.io https://*.europanb.net https://*.europanb.online https://app.europanb.online https://binderhub.europanb.online https://jupyterhub.europanb.online https://*.devsheds.io https://*.devsheds.net https://*.devsheds.online http://localhost:5000",
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-xsrftoken, ETag',
    'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,PATCH,OPTIONS',
    'Cache-Control': 'no-cache'
  }
}
# Unfortunately, only Python 3.8 has support for setting samesite cookies 
# in the stdlib. This is easily patched (Morsel._reserved['samesite'] = 
# 'SameSite'), but needing a patch is never great.
c.NotebookApp.cookie_options = {
    'samesite': 'none'
}


# remove path prefix that proxies through the JupyterHub Proxy 
# and jupyter-proxy-server
def fix_webview_url(path):
    try:
        i = path.index('/webview')
        print('Mapping path "{}" --> "{}"'.format(path, path[i:]))
        return path[i:]
    except:
        return path


c.ServerProxy.servers = {
    # initiated by supervisord instead; supervisord is initiated by the kubespawner post-start script
    # 'europa': {
    #     'command': ['sudo', '/bin/bash', '-i', 'python', '/root/europa/wsgi.py'],
    #     # 'command': ['sudo', '/usr/bin/supervisord', '-c', '/etc/supervisor/conf.d/supervisord.conf'],
    #     'port': 9003,
    #     'timeout': 180
    # },
    # 'theia': {
    #     'command': ['yarn', 'start', '/home/jovyan/work', '--hostname=0.0.0.0', '--port=9004'],
    #     'port': 9004,
    #     'absolute_url': False,
    #     'timeout': 180,
    #     'mappath': fix_webview_url
    # }
    # code-server
    'theia': {
        'command': ['code-server', '--auth=none', '--bind-addr=0.0.0.0:9004', '--disable-telemetry', '/home/jovyan/work'],
        'port': 9004,
        'absolute_url': False,
        'timeout': 180,
    }
}


def commit_changes(model, os_path, contents_manager, **kwargs):
    # while popen is a non-blocking function (meaning you can continue 
    # the execution of the program without waiting the call to finish),
    # check_call is blocking
    log = contents_manager.log
    workdir, filename = os.path.split(os_path)
    jupyterhub_user = os.getenv("JUPYTERHUB_USER")
    branch = 'europa-' + jupyterhub_user.split('-')[-1]
    try:
        # Note Do not use stdout=PIPE or stderr=PIPE with this function 
        # as that can deadlock based on the child process output volume. 
        # Use Popen with the communicate() method when you need pipes.
        sys.stdout.write('git add\n')
        # subprocess.check_call(
        #     ["git", "add", filename],
        #     cwd=workdir,
        #     stdout=sys.stdout
        # )
        # 
        # other files such as .gitignore are getting updated
        subprocess.check_call(
            ["git", "add", '.'],
            cwd=workdir,
            stdout=sys.stdout
        )

        sys.stdout.write('git commit\n')
        subprocess.check_call(
            ["git", "commit", "-m", "auto commit"],
            cwd=workdir,
            stdout=sys.stdout
        )

        # sys.stdout.write('git pull\n')
        # subprocess.check_call(
        #     ["git", "pull", "origin", branch],
        #     cwd=workdir,
        #     stdout=sys.stdout
        # )

        sys.stdout.write('git push\n')
        subprocess.check_call(
            ["git", "push", "origin", branch],
            cwd=workdir,
            stdout=sys.stdout
        )

    except Exception as e:
        log.error(e)

c.FileContentsManager.post_save_hook = commit_changes

# https://github.com/jupyter/notebook/issues/3130
c.FileContentsManager.delete_to_trash = False

# Set the log level by value or name.
c.JupyterHub.log_level = 'DEBUG'

c.Application.log_level = 'DEBUG'

# Enable debug-logging of the single-user server
c.Spawner.debug = True

# Generate a self-signed certificate
if 'GEN_CERT' in os.environ:
    dir_name = jupyter_data_dir()
    pem_file = os.path.join(dir_name, 'notebook.pem')
    try:
        os.makedirs(dir_name)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
            pass
        else:
            raise

    # Generate an openssl.cnf file to set the distinguished name
    cnf_file = os.path.join(os.getenv('CONDA_DIR', '/usr/lib'), 'ssl', 'openssl.cnf')
    if not os.path.isfile(cnf_file):
        with open(cnf_file, 'w') as fh:
            fh.write('''\
[req]
distinguished_name = req_distinguished_name
[req_distinguished_name]
''')

    # Generate a certificate if one doesn't exist on disk
    subprocess.check_call(['openssl', 'req', '-new',
                           '-newkey', 'rsa:2048',
                           '-days', '365',
                           '-nodes', '-x509',
                           '-subj', '/C=XX/ST=XX/L=XX/O=generated/CN=generated',
                           '-keyout', pem_file,
                           '-out', pem_file])
    # Restrict access to the file
    os.chmod(pem_file, stat.S_IRUSR | stat.S_IWUSR)
    c.NotebookApp.certfile = pem_file

# Change default umask for all subprocesses of the notebook server if set in
# the environment
if 'NB_UMASK' in os.environ:
    os.umask(int(os.environ['NB_UMASK'], 8))
