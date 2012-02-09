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
import posix1e
import pwd

from django.contrib.auth.models import User

from datastage.config import settings

def get_name(username):
    return pwd.getpwnam(username).pw_gecos.split(',')[0]

def get_members(group_name):
    group = grp.getgrnam(group_name)
    return set(group.gr_mem) | set(u.pw_name for u in pwd.getpwall() if u.pw_gid == group.gr_gid)

def sync_permissions():
    leaders = get_members('datastage-leader')
    members = get_members('datastage-member')
    collabs = get_members('datastage-collaborator')

    data_directory = settings.DATA_DIRECTORY
    
    datastage_user = pwd.getpwnam(settings.get('main:datastage_user'))

    # Force leaders to be superusers
    for username in leaders | members | collabs:
        user, _ = User.objects.get_or_create(username=username)
        user.is_staff = user.is_superuser = user.username in leaders
        user.save()


    for name in ('private', 'shared', 'collab'):
        path = os.path.join(data_directory, name)
        if not os.path.exists(path):
            os.makedirs(path)
        os.chown(path, datastage_user.pw_uid, datastage_user.pw_gid)
        os.chmod(path, 0755)

        for user in leaders | members:
            pw_user = pwd.getpwnam(user)

            path = os.path.join(data_directory, name, user)
            if not os.path.exists(path):
                os.makedirs(path)

            # Make sure the directory is owned by the right person
            os.chown(path, pw_user.pw_uid, pw_user.pw_gid)

            acl_text = 'u::rwx,g::-,o::-,m::rwx,u:datastage:rwx'

            if name in ('private', 'shared'):
                acl_text += ',g:datastage-leader:rx'
            if name == 'collab':
                acl_text += ',g:datastage-leader:rwx'

            if name == 'shared':
                acl_text += ',g:datastage-member:rx'
            if name == 'collab':
                acl_text += ',g:datastage-member:rwx'

            if name == 'collab':
                acl_text += ',g:datastage-collaborator:rx'

            for acl_type in (posix1e.ACL_TYPE_ACCESS, posix1e.ACL_TYPE_DEFAULT):
                posix1e.ACL(text=acl_text).applyto(path, acl_type)

            with open(os.path.join(path, 'permissions.txt'), 'w') as f:
                f.write("By default, this directory is accessible by the following people:\n\n")
                
                f.write(" * Its owner (%s; %s) has read and write permissions;\n" % (get_name(user), user))
                if name in ('private', 'shared'):
                    f.write(" * The following research group leaders have read permissions:\n")
                    for leader in sorted(leaders):
                        f.write("   - %s (%s)\n" % (get_name(leader), leader))
                if name == 'shared':
                    f.write(" * The following research group members also have read permissions:\n")
                    for member in sorted(members):
                        f.write("   - %s (%s)\n" % (get_name(member), member))
                if name == 'collab':
                    f.write(" * The following research group leaders and members have read and write permissions:\n")
                    for person in sorted(leaders | members):
                        f.write("   - %s (%s)\n" % (get_name(person), person))
                    f.write(" * The following collaborators have read permissions:\n")
                    for collab in sorted(collabs):
                        f.write("   - %s (%s)\n" % (get_name(collab), collab))

            os.chown(f.name, datastage_user.pw_uid, datastage_user.pw_gid)
            os.chmod(f.name, 0774)

if __name__ == '__main__':
    sync_permissions()