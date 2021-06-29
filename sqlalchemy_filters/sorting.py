# -*- coding: utf-8 -*-

from .exceptions import BadSortFormat, FieldNotFound, SortFieldNotFound
from .models import Field

SORT_ASCENDING = 'asc'
SORT_DESCENDING = 'desc'


class Sort(object):

    def __init__(self, sort_spec):
        self.sort_spec = sort_spec

        try:
            field_name = sort_spec['field']
            direction = sort_spec['direction']
        except KeyError:
            raise BadSortFormat(
                '`field` and `direction` are mandatory attributes.'
            )
        except TypeError:
            raise BadSortFormat(
                'Sort spec `{}` should be a dictionary.'.format(sort_spec)
            )

        if direction not in [SORT_ASCENDING, SORT_DESCENDING]:
            raise BadSortFormat('Direction `{}` not valid.'.format(direction))

        self.field_name = field_name
        self.direction = direction
        self.nullsfirst = sort_spec.get('nullsfirst')
        self.nullslast = sort_spec.get('nullslast')

    def format_for_sqlalchemy(self, table):
        direction = self.direction
        field_name = self.field_name

        field = Field(table, field_name)
        try:
            sqlalchemy_field = field.get_sqlalchemy_field()
        except FieldNotFound as e:
            raise SortFieldNotFound(e)

        if direction == SORT_ASCENDING:
            sort_fnc = sqlalchemy_field.asc
        elif direction == SORT_DESCENDING:
            sort_fnc = sqlalchemy_field.desc

        if self.nullsfirst:
            return sort_fnc().nullsfirst()
        elif self.nullslast:
            return sort_fnc().nullslast()
        else:
            return sort_fnc()


def apply_sort(query, sort_spec, table):
    """Apply sorting to a :class:`sqlalchemy.orm.Query` instance.

    :param sort_spec:
        A list of dictionaries, where each one of them includes
        the necesary information to order the elements of the query.

        Example::

            sort_spec = [
                {'model': 'Foo', 'field': 'name', 'direction': 'asc'},
                {'model': 'Bar', 'field': 'id', 'direction': 'desc'},
                {
                    'model': 'Qux',
                    'field': 'surname',
                    'direction': 'desc',
                    'nullslast': True,
                },
                {
                    'model': 'Baz',
                    'field': 'count',
                    'direction': 'asc',
                    'nullsfirst': True,
                },
            ]

        If the query being modified refers to a single model, the `model` key
        may be omitted from the sort spec.

    :returns:
        The :class:`sqlalchemy.orm.Query` instance after the provided
        sorting has been applied.
    """
    if isinstance(sort_spec, dict):
        sort_spec = [sort_spec]

    sorts = [Sort(item) for item in sort_spec]

    sqlalchemy_sorts = [sort.format_for_sqlalchemy(table) for sort in sorts]

    if sqlalchemy_sorts:
        query = query.order_by(*sqlalchemy_sorts)

    return query
