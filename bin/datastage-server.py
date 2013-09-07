
import errno
import multiprocessing
import os
import signal
import sys
import logging
import logging.config

import django.core.handlers.wsgi
from django.core.management import call_command
from django_longliving.management.commands.longliving import Command as LonglivingCommand
from flup.server.scgi import WSGIServer

from datastage.admin.util import check_pid
from datastage.config import settings

# This script was slightly cribbed from the concepts presented at
# http://code.activestate.com/recipes/278731-creating-a-daemon-the-python-way/

class DatastageServer(object):
    actions = ('start', 'stop', 'restart')
    redirect_to = getattr(os, 'devnull', '/dev/null')
    
    def __init__(self):
        self.pidfile_path = settings.relative_to_config(settings['server:pidfile'])
        self.port = int(settings['server:port'])

    def __call__(self, action=None):
        if action not in self.actions:
            sys.stderr.write("You must call this program with one of: %s" % ', '.join(self.actions))
            sys.exit(1)
        return getattr(self, action.replace('-', '_'))()

    def start(self):
        if check_pid(self.pidfile_path):
            sys.stderr.write("DataStage server already running; aborting.\n")
            sys.exit(1)

        if '--no-daemonize' not in sys.argv:
            pid = os.fork()
            if pid == 0:
                os.setsid()
                pid = os.fork()
                if pid == 0:
                    os.chdir('/')
                    os.umask(0)
                else:
                    os._exit(0)
            else:
                os._exit(0)

        with open(self.pidfile_path, 'w') as f:
            f.write(str(os.getpid()))

        if not 'DJANGO_SETTINGS_MODULE' in os.environ:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'datastage.web.settings'

        signal.signal(signal.SIGTERM, self.sigterm)
        signal.signal(signal.SIGINT, self.sigterm)
        
        # Create datastage.log for general logging
        directory = "/var/log/datastage"
        if not os.path.exists(directory):
           os.makedirs(directory)   
        genlogfile = open("/var/log/datastage/datastage.log",'w')
        genlogfile.close()
                
        logging.basicConfig(
            level = logging.DEBUG,
            format = '%(asctime)s %(levelname)s %(message)s',
            filename = '/var/log/datastage/datastage.log',
            filemode = 'w'
        )
        
        self.longliving_process = multiprocessing.Process(target=self.longliving_process_func)
        self.server_process = multiprocessing.Process(target=self.server_process_func)
        
        # Redirect stdin, stdout and stderr to /dev/null
        
        # First, close all open file descriptors
        for fd in range(0, 3):
            try:
                os.close(fd)
            except OSError:    # ERROR, fd wasn't open to begin with (ignored)
                pass

        # Next, open /dev/null as the first available fd (0)
        os.open(self.redirect_to, os.O_RDWR)    # standard input (0)

        # Duplicate standard input to standard output and standard error.
        os.dup2(0, 1)            # standard output (1)
        os.dup2(0, 2)            # standard error (2)

        self.longliving_process.start()
        self.server_process.start()
        self.longliving_process.join()
        self.server_process.join()

    def sigterm(self, signo, frame):
        self.longliving_process.terminate()
        self.server_process.terminate()

        self.longliving_process.join()
        self.server_process.join()

    def stop(self):
        with open(self.pidfile_path) as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError, e:
            if e.errno != errno.ESRCH:
                raise 
        
    
    def longliving_process_func(self):
        command = LonglivingCommand()
        command.handle(logfile='/var/log/datastage/datastage-longliving.log', loglevel='debug')

    def server_process_func(self):
        application = django.core.handlers.wsgi.WSGIHandler()
        WSGIServer(application, bindAddress=('localhost', self.port)).run()

if __name__ == '__main__':
    server = DatastageServer()
    server(*sys.argv[1:2])
