# -*- coding: utf-8 -*-
from django.core.cache import get_cache

from .conf import *

__all__ = ['simple_cache_result']

def simple_cache_result(**kwargs):
    cache_name = kwargs.get('cache',CORSCACHE_DECORATORS_CACHE)
    timeout = kwargs.get('timeout',3600)
    cache_key = kwargs.get('key',None)
    cache_prefix = kwargs.get('prefix','') or ''
    
    def _wrap_func(func):
        cache_key = '%s_%s__%s__%s' % (CORSCACHE_DECORATORS_PREFIX,cache_prefix,func.__class__.__name__,func.__name__)
        cache = get_cache(cache_name)
        def cached(*args,**kwargs):
            result = cache.get(cache_key)
            if result is None:
                result = func(*args,**kwargs)
                cache.set(cache_key,result,timeout)
            return result
        return cached
    return _wrap_func