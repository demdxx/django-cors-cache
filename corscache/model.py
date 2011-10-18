# -*- coding: utf-8 -*-

# TODO: Удалить и сделать аналогичную отчистку через Manager

from django.db.models import Model

from .blockmanager import base_cache_manager
from .conf import CORSCACHE_INTELLIGENCE, CORSCACHE_EXTENDET_LINKS

__all__ = ['ModelMixin']

class ModelMixin:
    def save(self,*args,**kwargs):
        # Отчистим кэшь для данного объекта и его связей
        if CORSCACHE_INTELLIGENCE:
            base_cache_manager.invalidate(self)
        if CORSCACHE_EXTENDET_LINKS:
            base_cache_manager.invalidate_by_extend_link_rules(self)
        return self._no_monkey.save(self,*args,**kwargs)

    def delete(self,*args,**kwargs):
        # Отчистим кэшь для данного объекта и его связей
        if CORSCACHE_INTELLIGENCE:
            base_cache_manager.invalidate(self)
        if CORSCACHE_EXTENDET_LINKS:
            base_cache_manager.invalidate_by_extend_link_rules(self)
        return self._no_monkey.delete(self,*args,**kwargs)
