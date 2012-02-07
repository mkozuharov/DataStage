import grp
import os
import posix1e
import pwd

from datastage.config import settings

def get_name(username):
    return pwd.getpwnam(username).pw_gecos.split(',')[0]

def sync_permissions():
    leaders = set(grp.getgrnam('datastage-leader').gr_mem)
    members = set(grp.getgrnam('datastage-member').gr_mem)
    collabs = set(grp.getgrnam('datastage-collaborator').gr_mem)

    data_directory = settings.DATA_DIRECTORY
    
    datastage_user = pwd.getpwnam(settings.get('main:datastage_user'))

    for user in leaders | members:
        for name in ('private', 'shared', 'collab'):
            path = os.path.join(data_directory, name, user)
            if not os.path.exists(path):
                os.makedirs(path)

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