# -*- coding: utf-8 -*-

from inspect import getmembers, ismethod

class MonkeyProxy(object):
    def __init__(self, cls):
        monkey_bases = tuple(b._no_monkey for b in cls.__bases__ if hasattr(b, '_no_monkey'))
        for monkey_base in monkey_bases:
            for name, value in monkey_base.__dict__.iteritems():
                setattr(self, name, value)


def monkey_mix(cls, mixin, methods=None):
    """
    Mixes a mixin into existing class.
    Does not use actual multi-inheritance mixins, just monkey patches methods.
    Mixin methods can call copies of original ones stored in `_no_monkey` proxy:

    class SomeMixin(object):
        def do_smth(self, arg):
            ... do smth else before
            self._no_monkey.do_smth(self, arg)
            ... do smth else after
    """
    assert '_no_monkey' not in cls.__dict__, 'Multiple monkey mix not supported'
    cls._no_monkey = MonkeyProxy(cls)

    if methods is None:
        methods = getmembers(mixin, ismethod)
    else:
        methods = [(m, getattr(mixin, m)) for m in methods]

    for name, method in methods:
        if hasattr(cls, name):
            setattr(cls._no_monkey, name, getattr(cls, name))
        setattr(cls, name, method.im_func)


