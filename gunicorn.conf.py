from gevent import monkey
monkey.patch_all()

bind = "0.0.0.0:8000"

workers = 3               # ESTO SOLUCIONA EL PROBLEMA
worker_class = "gevent"
worker_connections = 2000

timeout = 120
graceful_timeout = 30
keepalive = 2

max_requests = 2000
max_requests_jitter = 200

accesslog = "-"
errorlog = "-"
loglevel = "info"
