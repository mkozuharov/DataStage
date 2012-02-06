import grp
import os
import pwd
import re
import socket
import struct
import subprocess
import sys

import libmount

from datastage.config import settings
from .menu_util import interactive, menu, ExitMenu
from .util import check_pid

def get_ips():
    addrs = (re.findall(r"addr: ?([\d:.a-f]+)", subprocess.check_output('/sbin/ifconfig')))
    # Drop link-local addresses for IPv6, as they're uninteresting
    addrs = set(addr for addr in addrs if not addr.startswith('fe80:'))
    return addrs

def from_hex(value):
    return ''.join(chr(int(value[i:i+2], 16)) for i in range(0, len(value), 2))

def parse_addr(addr):
    if all(c == '0' for c in addr):
        return None # Listening on all interfaces
    if len(addr) == 8:
        return '.'.join(reversed([str(int(addr[i:i+2], 16)) for i in range(0, 8, 2)]))
    else:
        # Turn it into a binary string
        addr = from_hex(addr)
        # Use the magic of byte-ordering to move the bytes around, producing a hex string
        addr = ''.join(map('%08X'.__mod__, struct.unpack('<'+'l'*4, addr)))
        # Create a list of parts of the address, e.g ['2001', 'a02', ...]
        addr = [addr[i:i+4].lstrip('0') or '0' for i in range(0, len(addr), 4)]
        try:
            longest_zero_run = max((j-i, i, j) for i in range(0, len(addr)) for j in range(i+1, len(addr)+1) if all(x=='0' for x in addr[i:j]))
            start, end = longest_zero_run[1:3]
            return ':'.join(addr[:start]) + '::' + ':'.join(addr[end:])
        except ValueError:
            # No zeros in this address
            return ':'.join(addr)

def parse_port(port):
    return struct.unpack('>H', from_hex(port))[0]

def get_all_listening():
    listening = []
    for proto in ('tcp', 'udp', 'tcp6', 'udp6'):
        with open(os.path.join('/proc/net/', proto)) as f:
            sockets = [l.split()[1:3] for l in list(f)[1:]]
            for socket in sockets:
                (local_addr, local_port), (remote_addr, remote_port) = [x.split(':') for x in socket]
                local_addr, remote_addr = map(parse_addr, (local_addr, remote_addr))
                local_port, remote_port = map(parse_port, (local_port, remote_port))
                if remote_addr is not None:
                    continue # This isn't a listening socket
                listening.append((proto, local_addr, local_port))
    return listening

def check_port_listening(addrs, port):
    available_at = set()
    for addr in addrs:
        # Choose our IPv6 or IPv4 socket by inferring the address type.
        proto = socket.AF_INET6 if ':' in addr else socket.AF_INET
        s = socket.socket(proto, socket.SOCK_STREAM)
        s.setblocking(3)

        try:
            s.connect((addr, port))
            s.shutdown(2)
            available_at.add(addr)
        except Exception:
            pass
    return available_at



def firewall_menu():
    print "Hello!"
    yield
    
def samba_menu():
    print "SAMBA configuration"
    yield
    

def config_menu():
    def service_check(label, check_port, pid_filenames, service_name, firewall_ports):
        actions = {}
        listening_on = set()
        for proto, addr, port in listening:
            if port == check_port and proto.startswith('tcp'):
                if addr is None:
                    listening_on |= ips
                else:
                    listening_on.add(addr)
                    
        available_at = check_port_listening(listening_on, check_port)
        
        print
        if check_pid(*pid_filenames):
            print "%10s:  Status:       \033[92mRunning\033[0m" % label
            print "             Listening on: %s" % ', '.join(sorted(listening_on))
            print "             Available at: %s" % ', '.join(sorted(available_at))
            if listening_on != available_at:
                print "             Warning:      Not available on all interfaces."
                print "             \033[95mAction:       Type '%s' to tweak the firewall\033[0m" % service_name
                actions[service_name] = update_firewall_service(*firewall_ports)
        else:
            print "%10s:  Status:       \033[91mNot running\033[0m" % label
            print "             \033[95mAction:       Type '%s' to start %s\033[0m" % (service_name, label)
            actions[service_name] = enable_service(service_name, label)

        return actions

    while True:
        actions = {'refresh': lambda: None}
        listening = get_all_listening()
        ips = get_ips()
        
        print
        print "Status of some services"
        
        actions.update(service_check('SSH', 22,
                                     ['/var/run/sshd.pid'],
                                     'sshd', ['ssh/tcp']))
        actions.update(service_check('Apache', 80,
                                     ['/var/run/apache2.pid', '/var/run/httpd/httpd.pid'],
                                     'apache2', ['www/tcp']))
        
        if os.path.exists('/etc/apache2/sites-enabled/000-default'):
            print "             Warning:      Default site exists at /etc/apache2/sites-enabled/000-default"
            print "             \033[95mAction:       Type 'defaultsite' to remove it and restart Apache\033[0m"
            actions['defaultsite'] = remove_default_apache_site()
        
        actions.update(service_check('Samba', 445,
                                     ['/var/run/samba/smbd.pid'],
                                     'samba', ['netbios-ns/udp', 'netbios-dgm/udp',
                                               'netbios-ssn/tcp', 'microsoft-ds/tcp']))
        
        if SambaConfigurer.needs_configuring():
            print "             Warning:      Samba is not configured to serve DataStage files"
            print "             \033[95mAction:       Type 'confsamba' to configure and restart Samba\033[0m"
            actions['confsamba'] = SambaConfigurer()

        if FilesystemAttributes.needs_configuring():
            print "             Warning:      The filesystem frpm which DataStage will serve data is missing mount options "
            print "             \033[95mAction:       Type 'fs' to ensure the filesystem is mounted with acl and user_xattr options\033[0m"
            actions['fs'] = FilesystemAttributes()

        yield menu(actions)

def enable_service(name, label):
    def f():
        print "Enabling %s..." % label
        subprocess.call(["service", name, "start"])
        subprocess.call(["chkconfig", name, "on"])
        print "%s enabled." % label
    return f

def update_firewall_service(*names):
    def f():
        print "Tweaking the firewall"
        for name in names:
            subprocess.call(["/usr/sbin/ufw", "allow", name])
        subprocess.call(["/usr/sbin/ufw", "enable"])
        print "Tweaking complete"
    return f

def remove_default_apache_site():
    def f():
        print "Removing default apache site and restarting apache"
        os.unlink('/etc/apache2/sites-enabled/000-default')
        subprocess.call(["service", "apache2", "restart"])
        print "Done"
    return f

class SambaConfigurer(object):
    BLOCK_START = '# Start of DataStage configuration, inserted by datastage-config\n'
    BLOCK_END   = '# End of DataStage configuration\n'
    def __call__(self):
        print "HHH"
        with open('/etc/samba/smb.conf') as f:
            lines = list(f)
        try:
            first, last = lines.index(self.BLOCK_START), lines.index(self.BLOCK_END)
        except ValueError:
            lines.append('\n') # Add an extra blank line before our block
            first, last = len(lines), len(lines)
        lines[first:last] = [self.BLOCK_START,
                             '[datastage]\n',
                             '  comment = DataStage file area\n',
                             '  browseable = yes\n',
                             '  read only = no\n',
                             '  path = %s\n' % settings.DATA_DIRECTORY,
                             '  unix extensions = no\n',
                             '  create mask = 0700\n',
                             '  force create mode = 0700\n',
                             '  directory mask = 0700\n',
                             '  force directory mode = 0700\n',
                             '  valid users = @datastage-leader @datastage-member\n',
                             self.BLOCK_END]
        with open('/etc/samba/smb.conf', 'w') as f:
            f.writelines(lines)
        subprocess.call(["service", "samba", "restart"])

    @classmethod
    def needs_configuring(cls):
        if not os.path.exists('/etc/samba/smb.conf'):
            return False
        with open('/etc/samba/smb.conf') as f:
            lines = list(f)
        return not (cls.BLOCK_START in lines and cls.BLOCK_END in lines)

class FilesystemAttributes(object):
    OPTIONS = frozenset(['user_xattr','acl'])

    @classmethod
    def get_filesystem(cls):
        return libmount.get_current_mounts().find_fs_containing(settings.DATA_DIRECTORY)

    @classmethod
    def needs_configuring(cls):
        fs = cls.get_filesystem()
        return not ('user_xattr' in fs.options and 'acl' in fs.options)

    def __call__(self):
        #print "Updating /etc/fstab"
        #with libmount.FilesystemTable() as fstab:
        #    fs = fstab.find_fs_containing(settings.DATA_DIRECTORY)
        #    fs.options |= self.OPTIONS
        #    fstab.save()

        print "Remounting the filesystem with the necessary options"
        fs = self.get_filesystem()
        options = fs.options | frozenset(['remount']) | self.OPTIONS
        subprocess.call(['mount', fs.target, '-o', ','.join(options)])

        print "Filesystem configuration done."

def users_menu():
    while True:
        print "User management"
        print

        leaders = set(grp.getgrnam('datastage-leader').gr_mem)
        collabs = set(grp.getgrnam('datastage-collaborator').gr_mem)
        members = set(grp.getgrnam('datastage-member').gr_mem)

        all_users = leaders | collabs | members

        print "Username      Role"
        print "=================="
        for user in all_users:
            role = "leader" if user in leaders \
              else "member" if user in members \
              else "collaborator" 
            print "%<20s %s" % (user, role)
        if not all_users:
            print "--- There are currently no users defined ---"

        yield menu({'add': add_user,
                    'edit': edit_user,
                    'remove': remove_user})

def add_user():
    username, name, role = None, None, None

    print "Add user (press Ctrl-D to cancel)"

    while True:
        print
        if username:
            username = raw_input("Username [%s]: " % username) or username
        else:
            username = raw_input("Username: ")
        if name:
            name = raw_input("Name [%s]: " % name) or name
        else:
            name = raw_input("Name: ")

        role = menu({'leader': 'leader',
                     'collaborator': 'collaborator',
                     'member': 'member'},
                    with_quit=False,
                    question="What role should this user have?",
                    prompt="Pick one> ")

        print "\nCreating user with these details:"
        print "  Username: %s" % username
        print "  Name: %s" % name
        print "  Role: %s" % role
        yield menu({'yes': create_user(username, name, role),
                    'no': None},
                   question="Is this correct?",
                   prompt="Pick one> ")

def create_user(username, name, role):
    result = subprocess.call(['adduser', username, '--gecos', name])
    if result:
        yield ExitMenu(1)
    # Add to the right group
    subprocess.call(['usermod', '-a', '-G', 'datastage-%s' % role, username])

    yield ExitMenu(2)

def edit_user():
    pass

def remove_user():
    pass


def main_menu():
    print "Welcome to the interactive DataStage set-up system."
    print "==================================================="
    
    
    if os.getuid() != 0:
        print "This utility must be run as root."
        sys.exit(1)
    
    
    while True:
        print
        print "You should start by checking that the system configuration is correct"
        print "by typing 'c'."
        yield menu({'config': config_menu,
                    'users': users_menu})



def main():
    interactive(main_menu())

if __name__ == '__main__':
    main()