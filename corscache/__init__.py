# -*- coding: utf-8 -*-

VERSION = ('0', '0', '0')

__version__ = '.'.join(VERSION)
__author__ = 'demdxx@gmail.com'
__lincese__ = 'MIT'

from django.db.models import Model
from django.db.models.query import QuerySet

from .db import *
from .utils import *
from .conf import CORSCACHE_QUERYCACHE_ACTIVE, CORSCACHE_ACTIVE

def install_corscache():
    """Install Cors Cache"""
    monkey_mix(Model, ModelMixin)
    if CORSCACHE_QUERYCACHE_ACTIVE:
        monkey_mix(QuerySet, QuerySetMixin)

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

if CORSCACHE_QUERYCACHE_ACTIVE or CORSCACHE_ACTIVE:
    install_corscache()
