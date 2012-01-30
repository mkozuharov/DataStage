import dpam.pam

from django.contrib.auth import models as auth_models

class User(auth_models.User):
    class Meta:
        proxy = True
    def check_password(self, raw_password):
        return dpam.pam.authenticate(self.username, raw_password)
    

# Monkey-patch User model
auth_models.User = User
