# -*- coding: utf-8 -*-

import logging

try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import connections
from django.db.models import Model
from django.core.cache import get_cache
from django.utils.hashcompat import md5_constructor

from .conf import *
from .blockmanager import base_cache_manager
from .keystore import GroupKeyStore

__all__ = ['QuerySetMixin', 'ModelMixin']

logger = logging.getLogger(__name__)

keystore = GroupKeyStore(prefix=CORSCACHE_QUERYS_PREFIX,realstore=get_cache(CORSCACHE_KEYSTORE_CACHE))

QUERY_CACHE_OPTIONS = {}

def model_profile(model):
    module = model.__module__.split('.')[-2]
    key = ('%s.%s' % (module, model.__name__)).lower()

    if QUERY_CACHE_OPTIONS.has_key(key):
        return QUERY_CACHE_OPTIONS.get(key)

    #
    # Для правельного смешивания добавляем всё в 1 объект
    #
    options = {}
    options2 = {}
    options1 = CORSCACHE_QUERY_CACHE.get(key,{})
    options.update(options1)
    options1 = CORSCACHE_QUERY_CACHE.get('%s.*' % module,{})
    options2.update(options1)
    options2.update(options)
    options.update(options2)
    options1 = CORSCACHE_QUERY_CACHE.get('*.*',{})
    options2.update(options1)
    options2.update(options)
    options.update(options2)

    if not options.has_key('cache'):
        options['cache'] = CORSCACHE_DEFAULT_QUERY_CACHE

    QUERY_CACHE_OPTIONS[key] = None if not options.has_key('count') and not options.has_key('get') else options

    if QUERY_CACHE_OPTIONS[key]:
        if isinstance(QUERY_CACHE_OPTIONS[key]['cache'],basestring):
            QUERY_CACHE_OPTIONS[key]['cache'] = get_cache(QUERY_CACHE_OPTIONS[key]['cache'])

        if not QUERY_CACHE_OPTIONS[key].has_key('cache_get'):
            QUERY_CACHE_OPTIONS[key]['cache_get'] = QUERY_CACHE_OPTIONS[key]['cache']
        elif isinstance(QUERY_CACHE_OPTIONS[key]['cache_get'],basestring):
            QUERY_CACHE_OPTIONS[key]['cache_get'] = get_cache(QUERY_CACHE_OPTIONS[key]['cache_get'])

        if not QUERY_CACHE_OPTIONS[key].has_key('cache_count'):
            QUERY_CACHE_OPTIONS[key]['cache_count'] = QUERY_CACHE_OPTIONS[key]['cache']
        elif isinstance(QUERY_CACHE_OPTIONS[key]['cache_count'],basestring):
            QUERY_CACHE_OPTIONS[key]['cache_count'] = get_cache(QUERY_CACHE_OPTIONS[key]['cache_count'])

    return QUERY_CACHE_OPTIONS[key]


class QuerySetMixin(object):
    def __init__(self, *args, **kwargs):
        self._no_monkey.__init__(self, *args, **kwargs)
        self._nocache = True
        self._do_cache_get = False
        self._do_cache_count = False

        if not hasattr(self, '_cacheprofile') and self.model:
            self._cacheprofile = model_profile(self.model)
            if self._cacheprofile.has_key('get'):
                self._do_cache_get = True
            if self._cacheprofile.has_key('count'):
                self._do_cache_count = True
            if self._cacheprofile is not None:
                self._cache = self._cacheprofile.get('cache')
                self._nocache = False

    def _cache_key(self,params):
        md5 = md5_constructor()
        if isinstance(params,(list,tuple)):
            for i in params:
                md5.update(str(i))
        else:
            md5.update(str(params))
        return keystore.get_key(self.model._meta.db_table,md5.hexdigest())

    def _cache_results(self, cache_key, results, type):
        if cache_key:
            try:
                cache = self._cacheprofile.get('cache_'+type,self._cache)
                cache.set(cache_key,results,self._cacheprofile.get(type))
                return True
            except Exception, e:
                logger.exception(e)
        return False

    def _cache_link(self, key, key2, type):
        try:
            cache = self._cacheprofile.get('cache_'+type,self._cache)
            val = cache.get(key)
            if val:
                val = pickle.loads(val)
                try:
                    val.index(key2)
                except ValueError:
                    val.append(key2)
                    cache.set(key,pickle.dumps(val),3600*24*31)
            else:
                val = [key2]
                cache.set(key,pickle.dumps(val),3600*24*31)
        except Exception, e:
            logger.exception(e)

    #
    # Массовые действия
    #
    def delete(self):
        self._invalidate_table()
        return self._no_monkey.delete(self)
    delete.alters_data = True

    def update(self, **kwargs):
        self._invalidate_table()
        return self._no_monkey.update(self,**kwargs)
    update.alters_data = True

    def _update(self, values):
        self._invalidate_table()
        return self._no_monkey._update(self,values)
    _update.alters_data = True

    def get(self, *args, **kwargs):
        if self._nocache or not self._do_cache_get:
            return self._no_monkey.get(self, *args, **kwargs)

        cache_key = self._cache_key( ('get',) + tuple(sorted(kwargs.items())) )
        cache = self._cacheprofile.get('cache_get',self._cache)
        result = cache.get(cache_key)
        if result is not None:
            if not isinstance(result,Model):
                raise self.model.DoesNotExist("%s matching query does not exist."
                    % self.model._meta.object_name)
            return result

        try:
            result = self._no_monkey.get(self, *args, **kwargs)
        except self.model.DoesNotExist:
            result = False # Mark as not Exist!

        if cache_key:
            self._cache_results(cache_key,result,'get')
            # Link object to cache
            if isinstance(result,Model):
                self._cache_link(keystore.get_key(self.model._meta.db_table,'get:%s' % str(result.pk)),cache_key,'get')
            elif kwargs.has_key('id') or kwargs.has_key('pk'):
                self._cache_link(keystore.get_key(self.model._meta.db_table,'get:%s' % str(kwargs.get('id',kwargs.get('pk')))),cache_key,'get')

        if not isinstance(result,Model):
            raise self.model.DoesNotExist("%s matching query does not exist."
                    % self.model._meta.object_name)
            
        return result

    def get_or_create(self, *args, **kwargs):
        return self._no_monkey.get_or_create(self.nocache(), *args, **kwargs)

    def count(self, *args, **kwargs):
        result = None
        cache_key = False

        if not self._nocache and self._do_cache_count:
            try:
                cache_key = self._cache_key(('count',str(self.query)))
                cache = self._cacheprofile.get('cache_count',self._cache)
                result = cache.get(cache_key)
                if result is not None:
                    return result
            except Exception, e:
                logger.exception(e)

        result = self._no_monkey.count(self, *args, **kwargs)
        if cache_key:
            self._cache_results(cache_key,result,'count')
            # Link to table cache
            self._cache_link(keystore.get_key(self.model._meta.db_table,'count'),cache_key,'count')
        return result

    #
    # Инвалидация
    #
    def _invalidate_table(self):
        keystore.reset_key(self.model._meta.db_table)

    #
    # Вспомогательные
    #
    def nocache(self):
        qs = self._clone()
        qs._nocache = True
        return qs


def invalidate_model_object(obj):
    try:
        options = model_profile(obj.__class__)
        if options:
            # Clear linked cache objects
            if options.has_key('get'):
                key = keystore.get_key(obj._meta.db_table,'get:%s' % str(obj.pk))
                cache = options.get('cache_get')
                values = cache.get(key)
                if values:
                    cache.delete_many(pickle.loads(values)+[key])

            # Clear cache counts
            if options.has_key('count'):
                key = keystore.get_key(obj._meta.db_table,'count')
                cache = options.get('cache_count')
                values = cache.get(key)
                if values:
                    cache.delete_many(pickle.loads(values)+[key])

    except Exception, e:
        logger.exception(e)

if CORSCACHE_QUERYCACHE_ACTIVE:
    def __invalidate_object(self):
        # Отчистим кэшь для данного объекта и его связей
        if CORSCACHE_INTELLIGENCE:
            base_cache_manager.invalidate(self)
        if CORSCACHE_EXTENDET_LINKS:
            base_cache_manager.invalidate_by_extend_link_rules(self)
        invalidate_model_object(self)

else:
    def __invalidate_object(self):
        # Отчистим кэшь для данного объекта и его связей
        if CORSCACHE_INTELLIGENCE:
            base_cache_manager.invalidate(self)
        if CORSCACHE_EXTENDET_LINKS:
            base_cache_manager.invalidate_by_extend_link_rules(self)

class ModelMixin:
    def save(self,*args,**kwargs):
        self._invalidate()
        return self._no_monkey.save(self,*args,**kwargs)

    def delete(self,*args,**kwargs):
        self._invalidate()
        return self._no_monkey.delete(self,*args,**kwargs)

ModelMixin._invalidate = __invalidate_object


