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

import subprocess
import os
from datastage.config import settings


class SambaConfigurer(object):
    BLOCK_START = '# Start of DataStage configuration, inserted by datastage-config\n'
    BLOCK_END = '# End of DataStage configuration\n'

    def __call__(self):
        with open('/etc/samba/smb.conf') as f:
            lines = list(f)
        try:
            first, last = lines.index(self.BLOCK_START), lines.index(self.BLOCK_END)
        except ValueError:
            lines.append('\n') # Add an extra blank line before our block
            first, last = len(lines), len(lines)
        lines[first:last] = [self.BLOCK_START,
                             '[data]\n',
                             '  comment = DataStage file area\n',
                             '  browseable = yes\n',
                             '  read only = no\n',
                             '  path = %s\n' % settings.DATA_DIRECTORY,
                             '  unix extensions = no\n',
                             '  create mask = 0700\n',
                             '  force create mode = 0700\n',
                             '  directory mask = 0700\n',
                             '  force directory mode = 0700\n',
                             '  valid users = \n',
                             self.BLOCK_END]
        with open('/etc/samba/smb.conf', 'w') as f:
            f.writelines(lines)
        subprocess.call(["service", "smbd", "restart"])

    @classmethod
    def needs_configuring(cls):
        if not os.path.exists('/etc/samba/smb.conf'):
            return False
        with open('/etc/samba/smb.conf') as f:
            lines = list(f)
        return not (cls.BLOCK_START in lines and cls.BLOCK_END in lines)

    @classmethod
    def add_samba_groups(cls, groups):
        with open('/etc/samba/smb.conf') as f:
            lines = list(f)
        try:
            first, last = lines.index(cls.BLOCK_START), lines.index(cls.BLOCK_END)
        except ValueError:
            print "Samba not configured for datastage yet."
            return

        line = lines[last-1]
        line = line.split(' = ')
        conf_groups = line[1].strip()
        conf_groups = conf_groups.split(' ')
        conf_groups.extend(['@' + g for g in groups])
        line[1] = ' '.join(conf_groups) + '\n'
        line = ' = '.join(line)

        lines[last-1] = line
        with open('/etc/samba/smb.conf', 'w') as f:
            f.writelines(lines)
        subprocess.call(["service", "smbd", "restart"])

    @classmethod
    def remove_samba_groups(cls, groups):
        with open('/etc/samba/smb.conf') as f:
            lines = list(f)
        try:
            first, last = lines.index(cls.BLOCK_START), lines.index(cls.BLOCK_END)
        except ValueError:
            print "Samba not configured for datastage yet."
            return

        line = lines[last-1]
        line = line.split(' = ')
        conf_groups = line[1].strip()
        conf_groups = conf_groups.split(' ')
        conf_groups = [g for g in conf_groups if g not in ['@' + x for x in groups]]
        line[1] = ' '.join(conf_groups) + '\n'
        line = ' = '.join(line)

        lines[last-1] = line
        with open('/etc/samba/smb.conf', 'w') as f:
            f.writelines(lines)
        subprocess.call(["service", "smbd", "restart"])
