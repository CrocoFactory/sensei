from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass
from ._utils import is_self_method


class _Namespace(dict):
    def __setitem__(self, key, value):
        if is_self_method(value):
            try:
                finalizer = value.__func__.finalizer
                setattr(value, 'finalizer', finalizer)
            except AttributeError:
                pass
        super().__setitem__(key, value)


class _ModelMeta(ModelMetaclass):
    @classmethod
    def __prepare__(metacls, name, bases):
        return _Namespace()


class APIModel(BaseModel, metaclass=_ModelMeta):
    def __str__(self):
        return f'{self.__class__.__name__}({super().__str__()})'
