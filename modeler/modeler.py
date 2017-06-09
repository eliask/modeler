#! /usr/bin/env python
# -*- coding: utf-8 -*-
# modeler - Meta-masterdata management
import sys, yaml, re
from itertools import chain
from collections import namedtuple
#from repoze.lru import lru_cache

import flask_output
import sql_output

LogicalTable = namedtuple('LogicalTable', 'name localized id_type inverse_fks valid_type internal historized pk attributes'.split())
LogicalColumn = namedtuple('LogicalColumn', 'name localized valid_type type serial_type nullable fk unique pk'.split())
LogicalTie = namedtuple('LogicalTie', 'name valid_type fks'.split())
LogicalEnum = namedtuple('LogicalEnum', 'name id_type valid_type coded localized values'.split())
ForeignKey = namedtuple('ForeignKey', 'table ref_id name'.split())
InverseForeignKey = namedtuple('InverseForeignKey', 'table valid_type name'.split())

Tables=[]
Enums=[]
Ties=[]
class LazyFKType(object):
    def __init__(self, fk):
        self.fk = fk
    def __repr__(self):
        'Warning: Hacks ahead'
        if self.fk.ref_id == 'id':
            return 'int'
        for table in Tables:
            if table.name != self.fk.table: continue
            for col in table.pk:
                if col.name == self.fk.ref_id:
                    return col.type

        assert False, 'Could not find FK reference: {}'.format(self.fk)

class LazyInverseFKs(object):
    def __init__(self, table):
        self.table = table
    def __iter__(self):
        for table in Tables:
            for col in chain(table.pk, table.attributes):
                if col.fk and col.fk.table == self.table:
                    assert col.fk.ref_id == 'id'
                    yield InverseForeignKey(
                        table=table.name,
                        name=col.fk.name,
                        valid_type=col.valid_type,
                    )


def main_(table, _cols):
    modifiers = [x.strip() for x in _cols[0].split(',')]
    cols = _cols[1:]

    valid_type = 'tstzrange'
    for mod in modifiers:
        r = re.findall('(.*)\((.*)\)', mod)
        if r and r[0][0] == 'HISTORIZED':
            valid_type = r[0][1]
        else:
            assert not r, 'Unhandled modifier: {}'.format()

    historized = any(['HISTORIZED' in mod for mod in modifiers])
    # assert historized, (table, _cols)

    _columns = []

    if 'ENUM' in modifiers:
        assert len(cols) == 1, cols
        id_type = 'smallint' # by default
        values = cols[0] # int -> code
        del values['values']
        Enums.append(LogicalEnum(
            name=table,
            id_type=id_type,
            valid_type=valid_type,
            values=values,
            coded=True, # has a canonical code name? (non-localized)
            localized='LOCALIZED' in modifiers
        ))
        return

    if 'TIE' in modifiers:
        columns = []; fks=[]
        for col in cols:
            name, fk_text = col.items()[0]
            if name == 'valid':
                valid_type = fk_text
                continue
            r = re.findall('^references (.*)\((.*)\)', fk_text)
            _table, ref_id = r[0]
            fks.append(ForeignKey(_table, ref_id, name))

        Ties.append(LogicalTie(
            name=table,
            valid_type=valid_type,
            fks=fks,
        ))
        return

    table_localized = False
    pk = []
    for col in cols:
        assert len(col) == 1, col
        col_name, col_attrs = col.items()[0]
        dd={}
        r = re.findall('^references (.*)\((.*)\)(\s+<-> .*)?', col_attrs)
        if r:
            _table, ref_id, backref = r[0]
            dd['fk'] = ForeignKey(_table, ref_id, col_name)
            dd['type'] = LazyFKType(dd['fk'])
            # if backref: print >>sys.stderr, backref
        else:
            dd['fk'] = None
            dd['type'] = col_attrs.split()[0]

        dd['name'] = col_name
        dd['serial_type'] = dd['type']
        dd['nullable'] = re.search(r'\brequired\b', col_attrs) is None
        dd['valid_type'] = valid_type # TODO: support attribute-level exceptions
        dd['unique'] = re.search(r'\bunique\b', col_attrs) is not None
        dd['pk'] = re.search(r'\bprimary key\b', col_attrs) is not None
        dd['localized'] = re.search(r'\blocalized\b', col_attrs) is not None
        table_localized = table_localized or dd['localized']

        col = LogicalColumn(**dd)
        if dd['pk']:
            pk.append(col)
        else:
            _columns.append(col)

    if len(pk) == 0:
        pk.append(LogicalColumn(
            name='id',
            valid_type='tstzrange', #?
            type='int',
            serial_type='serial',
            nullable=False,
            fk=None,
            unique=True,
            pk=True,
            localized=False, # ?
        ))

    assert len(pk) > 0
    id_type = tuple(x.type for x in pk)

    Tables.append( LogicalTable(
        name=table,
        id_type=id_type,
        historized=historized,
        internal='INTERNAL' in modifiers,
        valid_type=valid_type,
        pk=pk,
        inverse_fks=LazyInverseFKs(table),
        attributes=_columns,
        localized=table_localized,
    ) )


if __name__ == '__main__':
    d = yaml.load(sys.stdin)
    for table, _cols in d.items():
        main_(table, _cols)

    if sys.argv[1] == 'flask':
        flask_output.main(Tables,Enums,Ties)
    if sys.argv[1] == 'sql':
        sql_output.main(Tables,Enums,Ties)
