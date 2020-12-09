import os
import sys
import time
import logging
import logging.handlers

import inspect

gLogger = logging.getLogger("DISCUM")

class LogLevel:
    INFO = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    DEFAULT = '\033[m'

class Logger:
    def __init__(self, debug = True):

        formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(funcName)s: '
        '%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
        log_std = logging.StreamHandler()
        log_std.setFormatter(formatter)

        if not os.path.exists('logs'):
            os.makedirs('logs')

        log_file = logging.handlers.RotatingFileHandler(
            filename="./logs/" + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + ".log",
            encoding='utf-8', mode='a', maxBytes=10**7, backupCount=5)
        log_file.setFormatter(formatter)

        if (debug):
            gLogger.setLevel(logging.DEBUG)
        else:
            gLogger.setLevel(logging.INFO)

        gLogger.addHandler(log_std)
        gLogger.addHandler(log_file)


    @staticmethod
    def LogMessage(msg, log_level=LogLevel.INFO):
        stack = inspect.stack()
        function_name = "({}->{})".format(str(stack[1][0].f_locals['self']).split(' ')[0], stack[1][3])
        print('{} [+] {} {}'.format(log_level, function_name, msg))
        print(LogLevel.DEFAULT) # restore console color


    def getLogger():
        return gLogger


log_debug    = gLogger.debug
log_info     = gLogger.info
log_warning  = gLogger.warning
log_err      = gLogger.error
log_critical = gLogger.critical