bind = "0.0.0.0:8000"

workers = 2
worker_class = "gthread"
threads = 4

timeout = 300
graceful_timeout = 60
keepalive = 2

max_requests = 2000
max_requests_jitter = 200

accesslog = "-"
errorlog = "-"
loglevel = "info"
