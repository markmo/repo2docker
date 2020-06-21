from gevent.pywsgi import WSGIServer

from app import app

http_server = WSGIServer(('', 8081), app)
http_server.serve_forever()
