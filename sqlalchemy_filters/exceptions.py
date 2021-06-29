# -*- coding: utf-8 -*-


class BadFilterFormat(Exception):
    pass


class BadSortFormat(Exception):
    pass


class FieldNotFound(Exception):
    pass


class FilterFieldNotFound(FieldNotFound):
    pass


class SortFieldNotFound(FieldNotFound):
    pass


class InvalidPage(Exception):
    pass
