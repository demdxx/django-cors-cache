# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import get_cache

class Command(BaseCommand):
    help = 'Clear cors cache data'
    args = '(null)+'
    
    def handle(self, **options):
        for c in getattr(settings,'CACHES',{}).keys():
            get_cache(c).clear()

