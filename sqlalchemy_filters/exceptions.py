# -*- coding: utf-8 -*-


class BadFilterFormat(Exception):
    pass


class BadSortFormat(Exception):
    pass


class BadLoadFormat(Exception):
    pass


class BadSpec(Exception):
    pass


class FieldNotFound(Exception):
    pass


class FilterFieldNotFound(FieldNotFound):
    pass


class SortFieldNotFound(FieldNotFound):
    pass


class BadQuery(Exception):
    pass


class InvalidPage(Exception):
    pass
