# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

import grp
import os
import re
import socket
import subprocess
import sys

from .menu_util import interactive, menu

def get_ips():
    return set(re.findall(r"addr: ?([\d:.a-f]+)", subprocess.check_output('/sbin/ifconfig')))

def check_port_listening(port, localhost=True):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(3)
    
    if localhost:
        ips = set(['127.0.0.1'])
    else:
        ips = get_ips()
    
    listening_on = set()
    for ip in ips:
        try:
            s.connect((ip, port))
            s.shutdown(2)
            listening_on.add(ip)
        except Exception:
            pass
    return listening_on, ips, (listening_on == ips)


def firewall_menu():
    print "Hello!"
    yield
    
def samba_menu():
    print "SAMBA configuration"
    yield

def status_menu():
    while True:
        print
        print "Status of some services"
        print

        actions = {}
        if check_port_listening(22)[2]:
            print "SSH: Running"
            if check_port_listening(22, False)[2]:
                print "SSH not listening on all interfaces; type 'ssh' to modify the firewall"
                actions['ssh'] = update_firewall_ssh
        else:
            print "SSH: Not running; type 'ssh' to turn it on."
            actions['ssh'] = enable_service('sshd', 'SSH')
        
        if check_port_listening(80)[2]:
            print "Apache: Running"
            if os.path.exists('/etc/apache/sites-enabled/000-default'):
                print "Apache default site exists at /etc/apache/sites-enabled/000-default;"
                print "  type 'apache' to remove it and restart Apache"
                actions['apache'] = remove_default_apache_site
        else:
            print "Apache: Not running; type 'apache' to turn it on."
            actions['apache'] = enable_service('apache2', 'Apache')

            
        yield menu(actions)

def enable_service(name, label):
    print "Enabling %s..." % label
    subprocess.call(["service", name, "start"])
    subprocess.call(["chkconfig", name, "on"])
    print "%s enabled." % label

def update_firewall_ssh():
    print "Tweaking the firewall"
    subprocess.call(["/usr/sbin/ufw", "allow", "OpenSSH"])
    subprocess.call(["/usr/sbin/ufw", "enable"])
    print "Tweaking complete"

def remove_default_apache_site():
    print "Removing defulat apache site and restarting apache"
    os.unlink('/etc/apache/sites-enabled/000-default')
    subprocess.call(["service", "apache2", "restart"])
    print "Done"

def main_menu():
    print "Welcome to the interactive DataStage set-up system."
    
    if os.getuid() != 0:
        print "This utility must be run as root."
        sys.exit(1)
    
    
    while True:
        yield menu({'firewall': firewall_menu,
                    'samba': samba_menu,
                    'status': status_menu})



if __name__ == '__main__':
    interactive(main_menu())