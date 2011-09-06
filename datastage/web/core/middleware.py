import pwd

import pam

class DataStageUser(object):
    _pw_user = None

    id = pk = None
    username = None
    first_name = None
    last_name = None
    email = None

    is_staff = None
    is_active = None
    is_superuser = None

    def __init__(self, request):
        self._pw_user = pwd.getpwnam(request.META.get('REMOTE_USER', 'alex'))
        self.username = self._pw_user.pw_name
        
        self.id = self.pk = self._pw_user.pw_uid
        names = self._pw_user.pw_gecos.split(' ', 1)
        self.first_name, self.last_name = names[0], (names[1] if len(names) > 1 else None)
        
    def is_anonymous(self): return False
    def is_authenticated(self): return True
    def get_full_name(self): return self._pw_user.pw_gecos
    def set_password(self, new_password): raise NotImplementedError
    def check_password(self, raw_password): return pam.authenticate(self.username, raw_password)
    def set_unusable_password(self): raise NotImplementedError
    def has_unusable_password(self): raise NotImplementedError
    
class UserMiddleware(object):
    def process_request(self, request):
        request.user = DataStageUser(request)