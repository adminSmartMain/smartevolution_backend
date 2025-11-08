# gunicorn.conf.py
import os
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
max_requests = 1000
max_requests_jitter = 100
#Logs
accesslog = "-"  # Log a stdout
errorlog = "-"   # Log a stdout
loglevel = "info"
#Logs para Django
pythonpath = os.getcwd()