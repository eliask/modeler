# -*- coding: utf-8 -*-
from itertools import chain
from modeler import ForeignKey, Tables
from functools import partial

from jinja2 import Environment, PackageLoader, StrictUndefined
env = Environment(
    loader=PackageLoader('modeler', '..'),
    undefined=StrictUndefined,
)

DEFAULT_LANGUAGE='en'

def non_nullable_verification(c):
    if hasattr(c,'nullable') and c.nullable:
        return '-- Null permitted'
    else:
        return "RAISE EXCEPTION 'Column ''{}'' is not nullable';".format(c.name)

# transaction_time type is currently hardcoded to tstzrange
T_CURRENT_TIME='current_timestamp'

def main(Tables, Enums, Ties):
    # Required:
    print 'create extension "btree_gist";'
    # Optional:
    print 'create extension "postgis";'

    create_enums(Enums)
    create_tables(Tables)
    create_ties(Tables, Ties)

def serial_id_type(id_type):
    assert isinstance(id_type, basestring), id_type
    return {
        'int':'serial',
        'smallint':'smallserial',
        'bigint':'bigserial'
    }[id_type]

def get_v_current_time(_expr,x):
    return 'current_date' if x.valid_type == 'daterange' else 'current_timestamp'
def get_t_current_time():
    return T_CURRENT_TIME

def typeof_fk(Tables, fk):
    assert type(fk).__name__ == ForeignKey.__name__, ForeignKey
    # assert fk.ref_id == 'id'
    for table in Tables:
        if table.name != fk.table: continue

        if fk.ref_id == 'id':
            assert len(table.id_type) == 1, table
            return table.id_type[0]

        for col in table.pk:
            if col.name == ref_id:
                assert False, 'Unhandled case: {}'.format(col)

    assert False, 'FK not found: {}'.format(fk)


def create_enums(Enums):
    for enum in Enums:
        print env.get_template('enum.sql.jinja2').render(
            enum=enum,
            table = enum.name,
            id_type=serial_id_type(enum.id_type),
            v_current_time=get_v_current_time(None,enum),
            t_current_time=get_t_current_time(),
        )


def create_ties(Tables, Ties):
    for tie in Ties:
        print env.get_template('tie.sql.jinja2').render(
            tie=tie,
            table = tie.name,
            typeof_fk=partial(typeof_fk, Tables),
            non_nullable_verification=non_nullable_verification,
            v_current_time=get_v_current_time(None,tie),
            t_current_time=get_t_current_time(),
        )


def create_tables(Tables):
    # First create only the surrogate key tables in order to make foreign key creation easy.
    for table in Tables:
        if table.internal:
             continue
        assert table.valid_type in ('daterange', 'tstzrange'), table.valid_type
        assert all([c.valid_type in ('daterange', 'tstzrange') for c in chain(table.pk, table.attributes)]), table
        print env.get_template('surrogate_table.sql.jinja2').render(table=table.name, table_=table)

    for table in Tables:
        if table.internal:
             continue
        print env.get_template('table.sql.jinja2').render(
            DEFAULT_LANGUAGE=DEFAULT_LANGUAGE,
            table_ = table,
            table = table.name,
            get_v_current_time=get_v_current_time,
            get_t_current_time=get_t_current_time,
            get_p_current_time=lambda expr,x: expr+'::date' if x.valid_type == 'daterange' else expr,
            non_nullable_verification=non_nullable_verification,
        )
