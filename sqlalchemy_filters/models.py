from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm.mapper import Mapper
import types

from .exceptions import BadQuery, FieldNotFound, BadSpec


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


def get_query_models(query):
    """Get models from query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :returns:
        A dictionary with all the models included in the query.
    """
    models = [col_desc['entity'] for col_desc in query.column_descriptions]
    if hasattr(query, "_join_entities"):  # sqlalchemy<1.4
        models.extend(mapper.class_ for mapper in query._join_entities)
    else:  # sqlalchemy>=1.4
        models.extend(
            mapper.class_ for mapper in query._compile_state()._join_entities
        )

    # account also query.select_from entities
    if (
        hasattr(query, '_select_from_entity') and
        (query._select_from_entity is not None)
    ):
        model_class = (
            query._select_from_entity.class_
            if isinstance(query._select_from_entity, Mapper)  # sqlalchemy>=1.1
            else query._select_from_entity  # sqlalchemy==1.0
        )
        if model_class not in models:
            models.append(model_class)

    return {model.__name__: model for model in models}


def get_model_from_spec(spec, query, default_model=None):
    """ Determine the model to which a spec applies on a given query.

    A spec that does not specify a model may be applied to a query that
    contains a single model. Otherwise the spec must specify the model to
    which it applies, and that model must be present in the query.

    :param query:
        A :class:`sqlalchemy.orm.Query` instance.

    :param spec:
        A dictionary that may or may not contain a model name to resolve
        against the query.

    :returns:
        A model instance.

    :raise BadSpec:
        If the spec is ambiguous or refers to a model not in the query.

    :raise BadQuery:
        If the query contains no models.

    """
    models = get_query_models(query)
    if not models:
        raise BadQuery('The query does not contain any models.')

    model_name = spec.get('model')
    if model_name is not None:
        models = [v for (k, v) in models.items() if k == model_name]
        if not models:
            raise BadSpec(
                'The query does not contain model `{}`.'.format(model_name)
            )
        model = models[0]
    else:
        if len(models) == 1:
            model = list(models.values())[0]
        elif default_model is not None:
            return default_model
        else:
            raise BadSpec("Ambiguous spec. Please specify a model.")

    return model


def get_model_class_by_name(registry, name):
    """ Return the model class matching `name` in the given `registry`.
    """
    for cls in registry.values():
        if getattr(cls, '__name__', None) == name:
            return cls


def get_default_model(query):
    """ Return the singular model from `query`, or `None` if `query` contains
    multiple models.
    """
    query_models = get_query_models(query).values()
    if len(query_models) == 1:
        default_model, = iter(query_models)
    else:
        default_model = None
    return default_model


def auto_join(query, *model_names):
    """ Automatically join models to `query` if they're not already present
    and the join can be done implicitly.
    """
    # every model has access to the registry, so we can use any from the query
    query_models = get_query_models(query).values()
    model = list(query_models)[-1]
    if hasattr(model, "_decl_class_registry"):  # sqlalchemy<1.4
        model_registry = model._decl_class_registry
    else:  # sqlalchemy>=1.4
        model_registry = model.registry._class_registry

    for name in model_names:
        model = get_model_class_by_name(model_registry, name)
        if model not in get_query_models(query).values():
            try:
                query = query.join(model)
            except InvalidRequestError:
                pass  # can't be autojoined
    return query
