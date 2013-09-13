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
import subprocess

from datastage.web.dataset.models import Project

from datastage.config import settings

def get_name(username):
    return pwd.getpwnam(username).pw_gecos.split(',')[0]

def get_members(group_name):
    group = grp.getgrnam(group_name)
    return set(group.gr_mem) | set(u.pw_name for u in pwd.getpwall() if u.pw_gid == group.gr_gid)


def group_exists(group_name):
    try:
        group = grp.getgrnam(group_name)
    except KeyError:
        return False

    if not group:
        return False
    else:
        return True


def sync_permissions():
    projects = Project.objects.all()
    for project in projects:
        leaders = project.leaders
        members = project.members
        collabs = project.collaborators

        data_directory = os.path.join(settings.DATA_DIRECTORY, project.short_name)
        datastage_user = pwd.getpwnam(settings.get('main:datastage_user'))

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)
        os.chown(data_directory, datastage_user.pw_uid, datastage_user.pw_gid)
        os.chmod(data_directory, 0755)

        # Force leaders to be superusers and enable web login for everyone
        for user in leaders | members | collabs:
            #user.is_staff = user.is_superuser = user in leaders
            user.is_superuser = user in leaders
            user.is_staff = True
            user.save()

        leaders_group = project.leader_group.name
        members_group = project.member_group.name
        collaborators_group = project.collaborator_group.name

        #create project groups if they do not exist
        for group in (leaders_group, members_group, collaborators_group):
            if not group_exists(group):
                subprocess.call(['groupadd', group])

        #sync users with groups
        for user in leaders:
            subprocess.call(['usermod', user.username,
                             '-a',
                             '-G', leaders_group])
        for user in members:
            subprocess.call(['usermod', user.username,
                             '-a',
                             '-G', members_group])
        for user in collabs:
            subprocess.call(['usermod', user.username,
                             '-a',
                             '-G', collaborators_group])

        for name in ('private', 'shared', 'collab'):
            path = os.path.join(data_directory, name)
            if not os.path.exists(path):
                os.makedirs(path)
            os.chown(path, datastage_user.pw_uid, datastage_user.pw_gid)
            os.chmod(path, 0755)

            for user in leaders | members:
                pw_user = pwd.getpwnam(user.username)

                path = os.path.join(data_directory, name, user.username)
                if not os.path.exists(path):
                    os.makedirs(path)

                # Make sure the directory is owned by the right person
                if user in leaders:
                    os.chown(path, pw_user.pw_uid, grp.getgrnam(leaders_group).gr_gid)
                if user in members:
                    os.chown(path, pw_user.pw_uid, grp.getgrnam(members_group).gr_gid)

                acl_text = 'u::rwx,g::-,o::-,m::rwx,u:datastage:rwx'

                if name in ('private', 'shared'):
                    acl_text += ',g:'+leaders_group+':rx'
                if name == 'collab':
                    acl_text += ',g:'+leaders_group+':rwx'

                if name == 'shared':
                    acl_text += ',g:'+members_group+':rx'
                if name == 'collab':
                    acl_text += ',g:'+members_group+':rwx'

                if name == 'collab':
                    acl_text += ',g:'+collaborators_group+':rx'

                for acl_type in [posix1e.ACL_TYPE_ACCESS, posix1e.ACL_TYPE_DEFAULT]:
                    posix1e.ACL(text=acl_text).applyto(str(path), acl_type)

                with open(os.path.join(path, 'permissions.txt'), 'w') as f:
                    f.write("By default, this directory is accessible by the following people:\n\n")

                    f.write(" * Its owner (%s; %s) has read and write permissions;\n" % (get_name(user.username), user.username))
                    if name in ('private', 'shared'):
                        f.write(" * The following research group leaders have read permissions:\n")
                        for leader in sorted(leaders):
                            f.write("   - %s (%s)\n" % (get_name(leader.username), leader.username))
                    if name == 'shared':
                        f.write(" * The following research group members also have read permissions:\n")
                        for member in sorted(members):
                            f.write("   - %s (%s)\n" % (get_name(member.username), member.username))
                    if name == 'collab':
                        f.write(" * The following research group leaders and members have read and write permissions:\n")
                        for person in sorted(leaders | members):
                            f.write("   - %s (%s)\n" % (get_name(person.username), person.username))
                        f.write(" * The following collaborators have read permissions:\n")
                        for collab in sorted(collabs):
                            f.write("   - %s (%s)\n" % (get_name(collab.username), collab.username))

                os.chown(f.name, datastage_user.pw_uid, datastage_user.pw_gid)
                os.chmod(f.name, 0774)

if __name__ == '__main__':
    sync_permissions()