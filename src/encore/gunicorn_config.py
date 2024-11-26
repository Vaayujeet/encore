"""Gunicorn Configuration"""

# Check https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing

bind = "0.0.0.0:8000"  # pylint: disable=invalid-name
workers = multiprocessing.cpu_count()
# accesslog = the access log file to write to. else write to sysout.
# errorlog = the error log file to write to. else write to syserr.
# loglevel = warning
# capture_output = True # Redirect stdout/stderr to specified file in errorlog.
# pidfile = A filename to use for the PID file.
# pythonpath = A comma-separated list of directories to add to the Python path.
