import errno
import grp
import os
import pwd

import posix1e

class InvalidAccess(Exception):
    pass

def is_subdirectory(subdirectory, path):
    return True

permission_map = {
    posix1e.ACL_READ: 'read',
    posix1e.ACL_WRITE: 'write',
    posix1e.ACL_EXECUTE: 'execute',
}

def _check_permission(acl, user, st, permissions):
    """
    Implements the POSIX.1e ACL algorithm.
    
    Takes a posix1e.ACL, a pw_struct (as returned by various pwd functions),
    the result of an os.stat() call, and the iterable of permissions to check.
    
    See <http://www.suse.de/~agruen/acl/linux-acls/linux-acls-final.pdf>, page
    three for details of the algorithm.
    """
    def test(entry, mask=None):
        if mask and not all(mask.permset.test(p) for p in permissions):
            return False
        return all(entry.permset.test(p) for p in permissions)
    
    def in_group(gid):
        try:
            return gid == user.pw_gid or \
                   user.pw_name in grp.getgrgid(gid).gr_mem
        except KeyError:
            return False

    mask = [e for e in acl if e.tag_type == posix1e.ACL_MASK]
    mask = mask[0] if mask else None

    if user.pw_uid == st.st_uid:
        entries = [e for e in acl if e.tag_type == posix1e.ACL_USER_OBJ]
        if entries:
            return test(entries[0])
    for entry in acl:
        if entry.tag_type == posix1e.ACL_USER and entry.qualifier == user.pw_uid:
            return test(entry, mask)

    group_matched = False
    for entry in acl:
        if (entry.tag_type == posix1e.ACL_GROUP_OBJ and in_group(st.st_gid)) or \
           (entry.tag_type == posix1e.ACL_GROUP and in_group(entry.qualifier)):
            group_matched = True
            if test(entry, mask): return True
    if group_matched:
        return False
    
    entries = [e for e in acl if e.tag_type == posix1e.ACL_OTHER]
    if entries:
        return test(entries[0])

    return False

def get_permissions(path, user, check_prefixes=False):
    user = pwd.getpwnam(user)
    parts = path.split(os.path.sep)
    prefixes = [os.path.sep.join(parts[:i+1]) or '/' for i in xrange(len(parts)-1)]
    
    if check_prefixes:
        for prefix in prefixes:
            acl = posix1e.ACL(file=prefix)
            st = os.stat(prefix)
            if not _check_permission(acl, user, st, (posix1e.ACL_EXECUTE,)):
                raise IOError(errno.EACCES, None, prefix)
    
    acl = posix1e.ACL(file=path.encode('utf-8'))
    st = os.stat(path)
    
    return set(p for p in (posix1e.ACL_READ, posix1e.ACL_WRITE, posix1e.ACL_EXECUTE) if \
               _check_permission(acl, user, st, (p,)))
    
def has_permission(path, user, permission):
    acl = posix1e.ACL(file=path)
    user = pwd.getpwnam(user)
    st = os.stat(path)
    return _check_permission(acl, user, st, (permission,))
            
    

def statinfo_to_dict(st):
    return dict((n, getattr(st, n)) for n in dir(st) if n.startswith('st_'))