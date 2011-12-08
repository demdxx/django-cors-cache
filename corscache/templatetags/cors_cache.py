# -*- coding: utf-8 -*-

__author__ = 'Ponomarev Dmitry <demdxx@gmail.com>'
__lincese__ = 'MIT'

from django.template import Library, Node, TemplateSyntaxError, VariableDoesNotExist
from django.template import resolve_variable
from django.utils.encoding import force_unicode
from django.core.cache import get_cache
from django.contrib.auth.models import AnonymousUser
from django.db.models import Model

from ..blockmanager import base_cache_manager
from ..conf import add_to_link_rules, CORSCACHE_ACTIVE

register = Library()

class CacheNode(Node):
    STALE_REFRESH = 1
    STALE_CREATED = 2
    def __init__(self, nodelist, expire_time, fragment_name, vary_on, cache, links, **kwargs):
        self.nodelist = nodelist
        self.stale_time = expire_time
        self.expire_time = expire_time + 300 # create a window to refresh
        self.fragment_name = fragment_name
        self.vary_on = vary_on
        self.cache = cache
        self.links = links

    def render(self, context):
        # Build a unicode key for this fragment and all vary-on's.
        
        if not CORSCACHE_ACTIVE:
            return self.nodelist.render(context)
        
        values = []
        for var in self.vary_on:
            #try:
            values.append(resolve_variable(var, context))
            #except VariableDoesNotExist:
            #    raise TemplateSyntaxError("No such variable: %s", var)

        cache_key = u'__'.join([self.fragment_name] + [force_unicode(getattr(var,'pk',var))+u':'+var.__class__.__name__ for var in values])
        cache_key_stale = cache_key + '.stale'

        if self.links:
            add_to_link_rules(cache_key,self.links,cache=self.cache)
            self.links = None

        cache = get_cache(self.cache)

        value = cache.get(cache_key)
        stale = cache.get(cache_key_stale)
        
        if stale is None:
            cache.set(cache_key_stale, self.STALE_REFRESH, 30) # lock
            value = None # force refresh
        if value is None:
            value = self.nodelist.render(context)
            cache.set(cache_key, value, self.expire_time)
            cache.set(cache_key_stale, self.STALE_CREATED, self.stale_time) # reset
        return value


def do_cache(parser, token, endparse='endcache', noda=CacheNode):
    """
    This will cache the contents of a template fragment for a given amount
    of time, but with the extra bonus of limiting the dog-pile/stampeding
    effect.

    You can easily replace the default template cache, just change the load
    statement from ``{% load cache %}`` to ``{% load cors_cache %}``.

    Usage::

        {% load cors_cache %}
        {% cache [expire_time] [fragment_name] [cache] [links] %}
            .. some expensive processing ..
        {% endcache %}

    This tag also supports varying by a list of arguments::

        {% load cors_cache %}
        {% cache [expire_time] [fragment_name] [var1] [var2] .. [cache] [links] %}
            .. some expensive processing ..
        {% endcache %}

    Each unique set of arguments will result in a unique cache entry.
    """
    nodelist = parser.parse((endparse,))
    parser.delete_first_token()
    tokens = token.contents.split()
    if len(tokens) < 3:
        raise TemplateSyntaxError(u"'%r' tag requires at least 2 arguments." % tokens[0])
    try:
        expire_time = int(tokens[1])
    except ValueError:
        raise TemplateSyntaxError(u"First argument to '%r' must be an integer (got '%s')." % (tokens[0], tokens[1]))
    
    cache = 'default'
    links = ''
    if len(tokens)>3:
        ntokens = []
        for item in tokens:
            if item[0:6]=='cache=':
                cache = item[6:]
            elif item[0:6]=='links=':
                links = item[6:]
            else:
                ntokens.append(item)

        tokens = ntokens

    return noda(nodelist, expire_time, tokens[2].strip('"'), tokens[3:], cache=cache, links=links)


class SmartCacheNode(Node):
    def __init__(self, nodelist, expire_time, fragment_name, vary_on, cache, links):
        #try:
        #    index = vary_on.index('notbind')
        #    vary_on.remove(index)
        #    self.not_bind = True
        #except ValueError:
        #    self.not_bind = False
        
        self.nodelist = nodelist
        self.cachetime = expire_time
        self.fragment_name = fragment_name
        self.vary_on = vary_on
        self.cache = cache
        self.links = links

    def render(self, context):
        # Build a unicode key for this fragment and all vary-on's.
        
        if not CORSCACHE_ACTIVE:
            return self.nodelist.render(context)

        values = []
        for var in self.vary_on:
            try:
                values.append(resolve_variable(var, context))
            except VariableDoesNotExist:
                raise TemplateSyntaxError("No such variable: %s", var)

        objects = [o for o in values if isinstance(o,(Model,AnonymousUser)) ]
        values = [v for v in values if not isinstance(v,(Model,AnonymousUser))]

        if not objects or len(objects)<1:
            raise TemplateSyntaxError(u'Smart cache mast have Model object links')
        
        group = u'__'.join([force_unicode(it) for it in [self.fragment_name]+values])

        if self.links:
            add_to_link_rules(group,self.links,cache=self.cache)
            self.links = None
        
        # Получить текущий кэшь
        value = base_cache_manager.get_register(group=group, objects=objects,cache=self.cache)
        
        if value is None:
            # Обновим кэшь
            value=self.nodelist.render(context)
            base_cache_manager.register(group=group, \
                    objects=objects,value=value,cache=self.cache,cachetime=self.cachetime)

        return value


def do_smart_cache(parser, token):
    """
    Usage::

        {% load cors_cache %}
        {% smart_cache [expire_time] [fragment_name] [ModelObjects] cache=level1 links=module.Model.field %}
            .. some expensive processing ..
        {% end_smart_cache %}

    This tag also supports varying by a list of arguments::

        {% load cors_cache %}
        {% smart_cache [expire_time] [fragment_name] [ModelObjects] [var1] [var2] .. cache=level1 links=module.Model.field %}
            .. some expensive processing ..
        {% end_smart_cache %}

    Each unique set of arguments will result in a unique cache entry.
    """
    return do_cache(parser, token, 'end_smart_cache', noda=SmartCacheNode)


register.tag('cache', do_cache)
register.tag('smart_cache', do_smart_cache)
