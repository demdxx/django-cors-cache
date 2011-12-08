# -*- coding: utf-8 -*-



class InvalidateMiddleware(object):
    def process_request(self, request):
        if request.REQUEST.get('invalidate_block'):
            pass
