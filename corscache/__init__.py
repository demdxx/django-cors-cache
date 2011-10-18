# -*- coding: utf-8 -*-

#
# TODO: Необходимо реализовать кэш запросов
#

VERSION = ('0', '0', '0')

__version__ = '.'.join(VERSION)
__author__ = 'demdxx@gmail.com'
__lincese__ = 'MIT'

from django.db.models import Manager, Model
from django.db.models.query import QuerySet, ValuesQuerySet, ValuesListQuerySet, DateQuerySet

from .query import *
from .model import *
from .utils import *

def install_corscache():
    """Install Cors Cache"""

    monkey_mix(Model, ModelMixin)
    #monkey_mix(Manager, ManagerMixin)
    monkey_mix(QuerySet, QuerySetMixin)
    #monkey_mix(ValuesQuerySet, QuerySetMixin, ['iterator'])
    #monkey_mix(ValuesListQuerySet, QuerySetMixin, ['iterator'])
    #monkey_mix(DateQuerySet, QuerySetMixin, ['iterator'])
    #monkey_mix(DateQuerySet, QuerySetMixin, ['iterator'])

    # Turn off caching in admin
    from django.contrib.admin.options import ModelAdmin
    def ModelAdmin_queryset(self, request):
        queryset = o_ModelAdmin_queryset(self, request)
        if queryset._cacheprofile is None:
            return queryset
        else:
            return queryset.nocache()
    o_ModelAdmin_queryset = ModelAdmin.queryset
    ModelAdmin.queryset = ModelAdmin_queryset

install_corscache()
