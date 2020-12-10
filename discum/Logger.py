import os
import sys
import time
import logging
import logging.handlers

def setLogger(name):
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(funcName)s: '
        '%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    log_std = logging.StreamHandler()
    log_std.setFormatter(formatter)

    log_dir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)) + "/../") + "/logs/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = logging.handlers.RotatingFileHandler(
        filename= log_dir + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + ".log",
        encoding='utf-8', mode='a', maxBytes=10**7, backupCount=5)
    log_file.setFormatter(formatter)

    logger = logging.getLogger(name)
    
    logger.setLevel(logging.INFO)

    logger.addHandler(log_std)
    logger.addHandler(log_file)
    return logger

def cfgLogger(debug = False):
    if (debug):
        gLogger.setLevel(logging.DEBUG)
    else:
        gLogger.setLevel(logging.INFO)


gLogger = setLogger("DISCUM")

log_debug    = gLogger.debug
log_info     = gLogger.info
log_warning  = gLogger.warning
log_err      = gLogger.error
log_critical = gLogger.critical