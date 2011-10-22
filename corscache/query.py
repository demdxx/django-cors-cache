# -*- coding: utf-8 -*-

class QuerySetMixin(object):
    def __init__(self, *args, **kwargs):
        self._no_monkey.__init__(self, *args, **kwargs)
        self._cloning = 1000

        if not hasattr(self, '_cacheprofile') and self.model:
            self._cacheprofile = None#model_profile(self.model)
            self._cache_write_only = False
            if self._cacheprofile is not None:
                self._cacheops = self._cacheprofile['ops']
                self._cachetimeout = self._cacheprofile['timeout']
            else:
                self._cacheops = None
                self._cachetimeout = None

    def get_cache_key(self,extra=''):
        return u''

    #
    # Массовые действия
    #
    def delete(self):
        self.invalidate_table()
        return self._no_monkey.delete(self)
    delete.alters_data = True

    def update(self, **kwargs):
        self.invalidate_table()
        return self._no_monkey.update(self,**kwargs)
    update.alters_data = True

    def _update(self, values):
        self.invalidate_table()
        return self._no_monkey._update(self,values)
    _update.alters_data = True

    #
    # Инвалидация
    #
    def invalidate_table(self):
        pass

    #
    # Вспомогательные
    #
    def nocache(self, clone=False):
        """
        Convinience method, turns off caching for this queryset
        """
        # cache profile not present means caching is not enabled for this model
        if self._cacheprofile is None:
            return self.clone() if clone else self
        else:
            return self.cache(ops=[], clone=clone)

    def clone(self):
        return self

    #def iterator(self, *args, **kwargs):
    #    return self._no_monkey.iterator(*args, **kwargs)

class ManagerMixin(object):
	pass


