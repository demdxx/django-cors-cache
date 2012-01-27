# -*- coding: utf-8 -*-

__author__ = 'Ponomarev Dmitry <demdxx@gmail.com>'
__lincese__ = 'MIT'

#
# Менеджер блоков кэша
# Объявляются через теги
#   smart_cache 3600 group=news news_object cache=cacke_name
#   ! В тег нельзя передовать просто ID, нужно именно объекты !

# При регистрации создаётся иерархия прилинкованных объектов и групп.
# Тэг выше создаёт группу и основной кэш, в итоге мы получаем.
#
# news__${id} - основной кэшь | ???, содержит структуру { [линкованные теги], "контент" } ???
# news__${classModule}:${className}__${id}__link - группа в которой указывается связь с основным тегом
# ${classModule}:${className}__groups - связь обэекта с возможными группами кэша. Используется для инвалидации по всем группам
#
# Если играющих объектов несколько:
#
#   smart_cache 3600 group=news user_object news_object cache=cacke_name
#
# news__${user_id}__${news_id}
# news__${classModule}:${className}__${news_id}__link > [news__${user_id}__${news_id},...]
# news__${classModule}:${className}__${user_id}__link > [news__${user_id}__${news_id},...]
# ${classModule}:${classNews}__groups > [news,...]
# ${classModule}:${classUser}__groups > [news,...]
#
# В кэше подобной структуры можно выставлять на длительный или безлимитный срок хранения.
#

#import logging

try:
    import cPickle as pickle
except:
    import pickle

from django.core.cache import get_cache
from django.contrib.auth.models import AnonymousUser

from .keystore import GroupKeyStore
from .conf import *

#logger = logging.getLogger(__name__)

class BlockCacheManager:
    def __init__(self,prefix=CORSCACHE_BLOCKS_PREFIX,cachetime=None,defaultcache=None,keystore=GroupKeyStore):
        self._cachetime = cachetime if cachetime else CORSCACHE_DEFAULT_TIME
        self._defaultcache = defaultcache if defaultcache else CORSCACHE_DEFAULT_CACHE
        self._keystore = keystore(prefix=prefix,realstore=get_cache(CORSCACHE_KEYSTORE_CACHE))

    def get_cache_object(self,cache):
        if isinstance(cache,basestring):
            return get_cache(cache)
        return cache if cache else get_cache(self._defaultcache)

    def prepare_key(self,group,key):
        return self._keystore.get_key(group,key)

    def cache_base_key(self,group,objects):
        """Генерация основного ключа"""
        values = []
        for o in objects:
            if isinstance(o,AnonymousUser):
                values.append('anonymous')
            elif not o:
                values.append('none')
            else:
                values.append(unicode(o.__class__.__name__)+u':'+unicode(o.pk))

        return self.prepare_key(group,u'__'.join(values))

    def get_cache_as_array(self,key,cache):
        # Get current value
        val = cache.get(key)
        if val is None:
            val = []
        else:
            try:
                val = pickle.loads(val)
            except:
                val = []
        return val

    def key_links_update(self,key,uplink,cache):
        """
        Обновление связки ключей
        """
        
        # Get current value
        val = self.get_cache_as_array(key,cache)
        result = True if len(val)>0 else -1

        # Save new
        try:
            val.index(uplink)
        except ValueError:
            val.append(uplink)
            cache.set(key,pickle.dumps(val),3600*24*31)

        return result

    def register_link(self,group,obj,base_key,cache):
        """
        Регистрируем связку с объектом
        """

        # Generate link key
        pk = u'anonymous' if isinstance(obj,AnonymousUser) else unicode(obj.pk)
        key = self.prepare_key(group,u'%s:%s__%s__link' % (obj.__class__.__module__,obj.__class__.__name__, pk))

        # Update current link
        if -1 == self.key_links_update(key,base_key,cache):
            # Update groups link if link is empty )
            gkey = u'%s:%s__groups' % (obj.__class__.__module__,obj.__class__.__name__)
            self.key_links_update(gkey,group,cache)

    def register(self,group,objects,value,cache=None,cachetime=None):
        """
        Регистрируем контент и связки для кэша
        """
        _cache = self.get_cache_object(cache)

        # Сгенерируем ключь
        _key = self.cache_base_key(group,objects)

        if value is None:
            return _cache.get(_key)

        # Обновим основной кэш
        _cache.set(_key,value,cachetime if cachetime else self._cachetime)

        # Обновление связей
        for o in objects:
            self.register_link(group,o,_key,_cache)

        return value

    def get_register(self,group,objects,cache=None):
        return self.register(group=group,objects=objects,value=None,cache=cache)

    def invalidate_group(self,group,cache=None):
        """
        Сброс всех блоков данной группы.
        Связи с группами остаются нетронутыми.
        """
        self._keystore.reset_key(group)

    def invalidate_group_by_object(self,group,obj,cache):
        # Групповая отчистка прилинкованных ключей
        
        if not obj:
            return False
        
        # Get cache backend
        cache = self.get_cache_object(cache)
        
        # Generate link key
        pk = u'anonymous' if isinstance(obj,AnonymousUser) else unicode(obj.pk)
        key = self.prepare_key(group,u'%s:%s__%s__link' % (obj.__class__.__module__,obj.__class__.__name__, pk))
        
        # Get invalidate keys
        keys = self.get_cache_as_array(key,cache)

        #logger.debug('[CORSCACHE] Invalidate group: %s', group)
        #logger.debug('[CORSCACHE] Link key: %s [%s]', key, keys)
        
        # Invalidate keys
        if keys and len(keys)>0:
            cache.delete_many(keys+[key])

    def invalidate(self,obj,cache=None):
        """
        Инвалидация всех зависимых кэшей.
            Действует только на указанный тип кэша
        """

        # Get cache backend
        cache = self.get_cache_object(cache)
        
        # Generate group cache
        _gkey = u'%s:%s__groups' % (obj.__class__.__module__,obj.__class__.__name__)
        
        # Get cache groups
        # Возможно будет лучше ( однозначно быстрее указывать группу в сетингах ) но пока будет так
        # 2 кэша связок + 1 основной кэш
        groups = self.get_cache_as_array(_gkey,cache)
        
        for g in groups:
            self.invalidate_group_by_object(g,obj,cache)

    def __invalidate_simple_rule(self,group,obj,link,cache):
        if link.has_key('name_fields'):
            # Модифицируем имя используя параметры в модели
            names = []
            for n in link.get('name_fields'):
                val = None
                for k in n.split('__'):
                    val = getattr(val if val else obj,k,None)
                names.append( unicode(val) )
            group = '__'.join([group]+names)

        if not link.get('links',False):
            # Если это тупой кэшь
            cache.delete(group)
        else:
            # Удаляем линки
            for l in link['links']:
                self.invalidate_group_by_object(group,getattr(obj,l,None),link.get('cache',cache))

    def invalidate_by_extend_link_rules(self,obj,cache=None):
        """
        Инвалидация объекта по правилам расширенных ( сторонних ) связей.
            Если этот объект изменён => следовательно связанные объекты изменены.
        """

        # Проверим сторонние линки
        rules = get_block_link_rules_by_object(obj)
        if rules:
            # Get cache backend
            cache = self.get_cache_object(cache)

            # Обходим группы
            for group, links in rules.iteritems():
                # Обходим связи инвалидации
                if isinstance(links,dict):
                    self.__invalidate_simple_rule(group,obj,links,cache)
                else:
                    for l in links:
                        if isinstance(l,dict):
                            self.__invalidate_simple_rule(group,obj,l,cache)
                        elif isinstance(l,(list,tuple)):
                            for l2 in l:
                                self.invalidate_group_by_object(group,getattr(obj,l2,None),cache)
                        else:
                            self.invalidate_group_by_object(group,getattr(obj,l,None),cache)


base_cache_manager = BlockCacheManager(CORSCACHE_BLOCKS_PREFIX)

