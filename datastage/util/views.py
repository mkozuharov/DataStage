from __future__ import absolute_import

import base64
import pickle

from django.conf import settings
from django.views.generic import View
import redis

class RedisView(View):
    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            self._redis = redis.Redis(**settings.REDIS_PARAMS)
        return self._redis
    
    # Utility methods for storing Python objects in redis
    def pack(self, value):
        return base64.b64encode(pickle.dumps(value))
    def unpack(self, value):
        return pickle.loads(base64.b64decode(value))