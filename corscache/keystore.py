# -*- coding: utf-8 -*-

__author__ = 'Ponomarev Dmitry <demdxx@gmail.com>'
__lincese__ = 'MIT'

from uuid import uuid4
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

try:
    import cPickle as pickle
except:
    import pickle

class KeyGen(object):
    def __init__(self,prefix):
        self._prefix = prefix

    def random_generator(self,prefix=''):
        """Creates a random unique id."""
        return self.gen_key(prefix+str(uuid4()))

    @staticmethod
    def _convert(x):
        if isinstance(x, unicode):
            return x.encode('utf-8')
        return str(x)

    @classmethod
    def _recursive_convert(klass, x, key):
        for item in x:
            if isinstance(item, (tuple, list)):
                klass._recursive_convert(item, key)
            else:
                key.update(klass._convert(item))

    def gen_key(self, *values):
        """Generate a key from one or more values."""
        key = md5()
        self.__class__._recursive_convert(values, key)
        return '%s:%s' % (self._prefix, key.hexdigest())


class GroupKeyStore(object):
    def __init__(self,prefix,keygen=KeyGen,realstore=None):
        """
        realstore - phisic or mem store
        """
        self._realstore = realstore
        self._keygen = keygen(prefix)
        self._keys = {}
        if self._realstore:
            try:
                self._keys = pickle.loads(self._realstore.get('storage_GroupKeyStore')) or {}
            except:
                self._keys = {}

    def set_key(self, group, key):
        self._keys[group] = key
        if self._realstore:
            # store keys if need restart server
            self._realstore.set('storage_GroupKeyStore',pickle.dumps(self._keys),0)

    def get_key(self, group, postfix=''):
        if not self._keys.has_key(group):
            self.set_key(group,self._keygen.gen_key(group))

        return '%s__%s' % (self._keys[group], postfix)

    def reset_key(self, group):
        if not self._keys.has_key(group):
            return True

        key = self._keys.get(group)
        if key!=self._keygen.gen_key(group):
            self.set_key(group,None)
        else:
            self.set_key(group,self._keygen.random_generator(group))


