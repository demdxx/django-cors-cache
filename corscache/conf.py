# -*- coding: utf-8 -*-

__author__ = 'Ponomarev Dmitry <demdxx@gmail.com>'
__lincese__ = 'MIT'

from django.conf import settings

#
# Базовые настройки как у всех кэшей
#
CORSCACHE_DEFAULT_TIME = getattr(settings,'CORSCACHE_DEFAULT_TIME',3600)
CORSCACHE_DEFAULT_CACHE = getattr(settings,'CORSCACHE_DEFAULT_CACHE','default')
CORSCACHE_DEFAULT_QUERY_CACHE = getattr(settings,'CORSCACHE_DEFAULT_CACHE',CORSCACHE_DEFAULT_CACHE)
CORSCACHE_KEYSTORE_CACHE = getattr(settings,'CORSCACHE_KEYSTORE_CACHE',CORSCACHE_DEFAULT_CACHE)
CORSCACHE_DECORATORS_CACHE = getattr(settings,'CORSCACHE_QUERYS_CACHE',CORSCACHE_DEFAULT_CACHE)

# Префиксы к именам кэша
CORSCACHE_BLOCKS_PREFIX = getattr(settings,'CORSCACHE_BLOCKS_PREFIX','blocks')
CORSCACHE_QUERYS_PREFIX = getattr(settings,'CORSCACHE_QUERYS_PREFIX','querys')
CORSCACHE_DECORATORS_PREFIX = getattr(settings,'CORSCACHE_QUERYS_PREFIX','decorators')

#
# Интелект - автоматическая отчистка связанных блоков.
# Если отчистка построена только на правилах то лучше выключить.
#
CORSCACHE_INTELLIGENCE = getattr(settings,'CORSCACHE_INTELLIGENCE',True)

CORSCACHE_ACTIVE = getattr(settings,'CORSCACHE_ACTIVE',True)
CORSCACHE_QUERYCACHE_ACTIVE = getattr(settings,'CORSCACHE_QUERYCACHE_ACTIVE',CORSCACHE_ACTIVE)

#
# Правила кэширования запросов
#
# EXAMPLE:
#
#   CORSCACHE_QUERY_CACHE = {
#       'auth.user':{'get':3600},
#       'profile.profile':{'get':3600},
#       '*.*': {'count':3600,'cache':'level1'},
#   }
#
CORSCACHE_QUERY_CACHE = getattr(settings,'CORSCACHE_QUERY_CACHE',None)
if not CORSCACHE_QUERY_CACHE:
    CORSCACHE_QUERYCACHE_ACTIVE = False

#
# Сторонние связки. [ Карта инвалидации ]
#
# Иногда невозможно реализовать динамическую привязку блока к объекту,
# Просто потому что это неимеет никакого смысла
# Ведь наша задача ограничить число запросов,
# и вот здесь помогут связки объекта с блоками.
#
# Определим какой объект должен влиять на блок
#
# 'news.article': { 'news': {'links':('user',),'cache':'cacheName'}, 'catalog.product': ('section',) }
# Он влияет на блок новостей посредством своей связи с пользователем.
# В этом случае блок у нас объявлен как:
#
# {% smart_cache "news" autor cache=cacheName %} ... {% end_smart_cache %}
#
# При изменении или создании новости сбрасывается кэш этой группу связанный с пользователем
#

CORSCACHE_EXTENDET_LINKS = getattr(settings,'CORSCACHE_EXTENDET_LINKS',{}) or {}

def get_block_link_rules(module,klass,group=None):
    key = '%s.%s' % (module,klass)
    key = key.lower()
    if CORSCACHE_EXTENDET_LINKS.has_key(key):
        rules = CORSCACHE_EXTENDET_LINKS.get(key)
        return rules.get(group,None) if group else rules
    return None

def get_block_link_rules_by_object(obj,group=None):
    return get_block_link_rules(u'.'.join(obj.__class__.__module__.split('.')[:-1]),obj.__class__.__name__,group)

def add_to_link_rules(name,links,cache):
    """
    Для реализации тегов со сложными составными именами
    возможно их генерить и сохранять в карту через теги
        {% smart_cache ... links=module.model.field,module2.model2.field2...

    Также можно переложить усилия по созданию карт на эту фичу, если не использовать составные имена.
    Это гораздо удобнее но не совсем правильно ( но на производительность это не должно повлиять )

        Не переусерствуйте с этим инструментом
        
        Опасная штука к стати )))
    """
    if not links:
        return False
    
    links = links.strip('"').split(',') if isinstance(links,basestring) else links
    for l in links:
        splited = l.split('.')
        if len(splited)==3:
            modname = '%s.%s' % (splited[0],splited[1])
            if not CORSCACHE_EXTENDET_LINKS.has_key(modname):
                CORSCACHE_EXTENDET_LINKS[modname] = {}
            CORSCACHE_EXTENDET_LINKS[modname][name] = {'links':[splited[2]],'cache':cache}
        elif len(splited)==2:
            modname = splited
            if not CORSCACHE_EXTENDET_LINKS.has_key(modname):
                CORSCACHE_EXTENDET_LINKS[modname] = {}
            CORSCACHE_EXTENDET_LINKS[modname][name] = {'cache':cache}

