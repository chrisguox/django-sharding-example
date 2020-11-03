"""
MIT License

Copyright (c) 2020 iTraceur

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

===============================================================================
The MIT License applies to this file only.

"""
from contextlib import closing

from django.db import ProgrammingError
from django.db import connection

_shard_tables = {}


def generate_db_table_name(model, sharding):
    db_table = "_".join(
        map(str, [f"{model._meta.app_label}", model._meta.db_table, sharding]))

    return db_table


def register_model(abstract_model, sharding, meta_options=None):
    model_name = abstract_model.__name__ + sharding

    table_name = generate_db_table_name(abstract_model, sharding)

    class Meta:
        db_table = table_name

    for k, v in abstract_model._meta.__dict__.items():
        if k.startswith('__') or k in ('abstract', 'db_table'):
            continue

    if meta_options is None:
        meta_options = {
            'verbose_name':
            getattr(abstract_model._meta, "verbose_name",
                    abstract_model.__name__) + sharding,
            'verbose_name_plural':
            (getattr(abstract_model._meta, "verbose_name_plural",
                     abstract_model.__name__) + sharding)
        }

    for k, v in meta_options.items():
        setattr(Meta, k, v)

    attrs = {
        '__module__': abstract_model.__module__,
        'Meta': Meta,
    }

    _shard_tables[table_name] = type(model_name, (abstract_model, ), attrs)


def register_models(model):
    """
    可以使用修饰器的方式来实现，
    可以参考django @register

    :param model:
    :return:
    """
    for sharding_number in model.get_sharding_list():
        register_model(model, sharding_number)


class ShardingMixin(object):
    @classmethod
    def shard(cls, sharding_source=None, raise_exception=False):
        sharding = cls.get_sharding(str(sharding_source),
                                    raise_exception=raise_exception)

        db_table = cls.get_db_table(sharding)

        return _shard_tables[db_table]

    @classmethod
    def get_db_table(cls, sharding):
        db_table = generate_db_table_name(cls, sharding)

        if db_table not in _shard_tables:
            register_model(cls, sharding)

        with closing(connection.cursor()) as cursor:
            tables = [
                table_info.name for table_info in
                connection.introspection.get_table_list(cursor)
            ]

        if db_table not in tables:
            raise ProgrammingError(f"relation {db_table} does not exist")

        return db_table

    @classmethod
    def get_sharding(cls, sharding_source=None, raise_exception=False):
        sharding_source = cls.calc_sharding_source(sharding_source)

        sharding_list = cls.get_sharding_list()
        if sharding_source not in sharding_list:
            if raise_exception:
                raise ValueError(f"{sharding_source} not in sharding list")
            else:
                sharding_source = cls.get_default_sharding_source()

        return sharding_source

    @classmethod
    def get_default_sharding_source(cls):
        raise NotImplementedError

    @classmethod
    def get_sharding_list(cls):
        raise NotImplementedError

    @classmethod
    def calc_sharding_source(cls, sharding_source):
        raise NotImplementedError


class PreciseShardingMixin(ShardingMixin):
    DEFAULT_SHARDING_NUMBERS = 8

    @classmethod
    def get_default_sharding_source(cls):
        number = "0"
        return number

    @classmethod
    def get_sharding_list(cls):
        """
        generate sharding list with numbers
        """
        sharding_numbers = getattr(cls, '_SHARDING_NUMBERS',
                                   cls.DEFAULT_SHARDING_NUMBERS)

        return list(map(str, range(sharding_numbers)))

    @classmethod
    def calc_sharding_source(cls, sharding_source):
        sharding_numbers = getattr(cls, '_SHARDING_NUMBERS',
                                   cls.DEFAULT_SHARDING_NUMBERS)

        sharding_source = str(int(sharding_source) % sharding_numbers)

        return sharding_source
