import types

from .exceptions import FieldNotFound


class Field(object):

    def __init__(self, table, field_name):
        self.table = table
        self.field_name = field_name

    def get_sqlalchemy_field(self):
        if type(self.field_name) is str:
            if self.field_name not in self.table.c:
                raise FieldNotFound(
                    'Table {} has no column `{}`.'.format(
                        self.table, self.field_name
                    )
                )
            sqlalchemy_field = getattr(self.table.c, self.field_name)
        else:
            sqlalchemy_field = self.field_name

        # If it's a hybrid method, then we call it so that we can work with
        # the result of the execution and not with the method object itself
        if isinstance(sqlalchemy_field, types.MethodType):
            sqlalchemy_field = sqlalchemy_field()

        return sqlalchemy_field


def get_table(query):
    from_clauses = query.froms
    if len(from_clauses) > 1:
        raise NotImplementedError(
            "Support for multi-table queries is not implemented."
        )
    if len(from_clauses) == 0:
        raise NotImplementedError(
            "Support for no-table queries is not implemented."
        )
    return from_clauses[0]
