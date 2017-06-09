# -*- coding: utf-8 -*-
import re

Prefix_text='''import flask.ext.security as security
import sqlalchemy as sa
import datetime as dt
import sqlalchemy.types as types
from geoalchemy2.types import Geography, Geometry
from flask.ext.security import current_user
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql.json import (
    JSON,
)
from sqlalchemy.dialects.postgresql import (
    UUID,
    INET,
    MACADDR,
    BYTEA,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from flask.ext.principal import Permission, RoleNeed
from collections import namedtuple

from bat.types import *

db = SQLAlchemy()

class API(object): pass
class AttributeLogMixin(object): pass
class LogicalEnum(object): pass

_fields = []
def IColumn(*a, **kw):
    col = db.Column(*a, **kw)
    _fields.append(col)
    return col
def IRelationship(*a, **kw):
    r = db.relationship(*a, **kw)
    _fields.append(r)
    return r
CustomView = namedtuple('CustomView', ['name', 'url', 'remote'])
def ICustomView(*a, **kw):
    view = CustomView(*a, **kw)
    _fields.append(view)
    return view
class FormElement(object):
    "A dummy class for specifying extra form elements for models."
    def __init__(self):
        _fields.append(self)

class Header(FormElement):
    def __init__(self, title):
        FormElement.__init__(self)
        self.title = 'BK-' + title.lower().replace(' ', '-')
    def to_dict(self):
        return {'element': 'header', 'title': self.title}
class HiddenSection(FormElement):
    def to_dict(self):
        return {'element': 'hidden-section'}

class MetadataMixin(object):
    metadata_ = db.Column(db.Integer, nullable=False, default=0, name='metadata')
class Base(object):
    column_exclude_list = 'deleted',
    # column_searchable_list = sort_columns = 'name',
    def __unicode__(self): return self.name
    def __init__(self, **kwargs):
        """Set object attributes from keyword arguments directly

        Usage:
        >>> Person(email='foo@bar.com', first_names='Foo Baz')
        >>> Organization(description='??')
        """
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

class Language(db.Model):
    __tablename__ = 'language_iso639'
    code = db.Column(db.Unicode(2), primary_key=True)
    code3 = db.Column(db.Unicode(3), nullable=False)
    def __repr__(self):
        return dict(
            en='English',
            zh='Chinese',
        )[self.code]


class Localized(object):
    @declared_attr
    def language_code(self):
        return db.Column(db.Unicode(2), db.ForeignKey('language_iso639.code'), name='_language', primary_key=True)
    @declared_attr
    def language(self):
        return IRelationship(Language)


class User(Base, db.Model, security.UserMixin, API, MetadataMixin):
    __tablename__ = 'l_US_user'
    metadata_ = db.Column(db.Integer, nullable=False, default=0, name='metadata')
    id = IColumn(db.Integer(), primary_key=True)

    organization_id = IColumn(db.Integer, db.ForeignKey('l_OR_organization.id'), nullable=False)
    organization = IRelationship(lambda:Organization, foreign_keys=[organization_id], backref='users')

    email = IColumn(db.Unicode(254), nullable=False, unique=True)
    password = IColumn(db.Unicode(255), nullable=False)
    active = IColumn(db.Boolean())
    confirmed_at = IColumn(db.DateTime())

    roles = frozenset([]) # Stub for Flask-Security
    role = IColumn(RoleType, nullable=False)

class Role(Base, db.Model, security.RoleMixin, MetadataMixin):
    __tablename__ = 'l_RO_role'
    "Note: Dummy model. Not used anymore."
    __tablename__ = 'role'
    # metadata_ = db.Column(db.Integer, nullable=False, default=0, name='metadata')
    id = IColumn(db.Integer(), primary_key=True)
    name = IColumn(db.Unicode(200), unique=True, nullable=False)
    description = IColumn(db.Unicode(10000))
'''

sqla_types=dict(
    email='db.Unicode',
    integer='db.Integer',
    pos_integer='db.Integer',
    pos_smallint='db.SmallInteger',
    positive16='db.SmallInteger',
    positive32='db.Integer',
    int='db.Integer',
    smallint='db.SmallInteger',
    nonneg_smallint='db.SmallInteger',
    url='db.Unicode',
    varchar='db.Unicode',
    point='Point',
    polygon='Polygon',
    timestamptz='db.DateTime(timezone=True)',
    timestamp='db.DateTime',
    daterange='DATERANGE',
    tsrange='TSRANGE',
    tstzrange='TSTZRANGE',
    json='JSON',
    jsonb='JSON', # TODO 9.4
    bytea='BYTEA',
    boolean='db.Boolean',
)
sqla_types['char(2)'] = 'db.Unicode(2)'
sqla_types['char(3)'] = 'db.Unicode(3)'
sqla_types['"RoleType"'] = "RoleType"

# sqla_types['geometry(point)'] = "Geometry('POINT')"
# sqla_types['geometry(point,4326)'] = "Geometry('POINT', srid=4236)"
# sqla_types['geometry(polygon)'] = "Geometry('POLYGON')"
# sqla_types['geometry(polygon,4326)'] = "Geometry('POLYGON', srid=4236)"
# sqla_types['geometry(4326)'] = "Geometry(srid=4236)"

sqla_types['geometry(point)'] = "Point"
sqla_types['geometry(point,4326)'] = "Point"
sqla_types['geometry(polygon)'] = "Polygon"
sqla_types['geometry(polygon,4326)'] = "Polygon"
sqla_types['geometry(4326)'] = "Polygon"

def get_class_name(x):
    clsName = re.sub('^[A-Z]*_', '', x)
    return reduce(lambda x,y:x+y, [x[0].upper() + x[1:] for x in clsName.split('_')])

def format_col(localized_tables, x):
    type_ = sqla_types.get(x.type)
    if not type_:
        if isinstance(x.type, basestring):
            type_ = x.type.replace('varchar', 'db.Unicode')
        else:
            type_ = sqla_types[str(x.type)]

    attrs = ''; suffix=''
    if x.fk:
        attrs += ", db.ForeignKey('{loc_prefix}l_{table}.{ref_id}')".format(
            loc_prefix ='loc_' if x.fk.table in localized_tables else '',
            table=x.fk.table,
            ref_id=x.fk.ref_id,
        )
        suffix = "\n    {col_rel} = IRelationship(lambda:{table}, foreign_keys=[{col}])".format(
            table = get_class_name(x.fk[0]),
            col = x.name,
            col_rel = re.sub('_id$', '', x.name) if '_id' in x.name else x.name + '_',
        )

    if not x.nullable:
        attrs += ', nullable=False'

    return '{col} = IColumn({type_}{attrs}){suffix}'.format(
        col = x.name,
        type_ = type_,
        attrs = attrs,
        suffix = suffix,
    )

def get_enums_text(Enums):
    for enum in Enums:
        yield '''
class {clsName}(Base, db.Model, LogicalEnum, API, MetadataMixin):
    __tablename__ = 'l_{table}'
    valid_time = db.Column({valid_type})
    id = IColumn(db.SmallInteger, primary_key=True)
    name = IColumn(db.Unicode, nullable=False, unique=True)
'''.format(
    table=enum.name,
    clsName=get_class_name(enum.name),
    valid_type = sqla_types[enum.valid_type],
)

def get_ties_text(Ties, localized_tables):
    for x in Ties:
        columns = (
            "    IColumn('{col}', {type_}, db.ForeignKey('{loc_prefix}l_{table}.{ref}'), primary_key=True),".format(
                col=name,
                table=_table,
                type_='db.Integer', # TODO
                ref=ref_id,
                loc_prefix = 'loc_' if _table in localized_tables else '',
            )
            for _table,ref_id,name in x.fks
        )

        yield """
{table} = db.Table('l_{table}', db.Model.metadata,
    db.Column('metadata', db.Integer, nullable=False, default=0),
    db.Column('valid_time', {valid_type}),
{columns}
)""".format(
    columns='\n'.join(columns),
    table=x.name,
    valid_type = sqla_types[x.valid_type],
)


def get_table_ties(Ties, table):
    for x in Ties:
        if any([t==table for t,ref,name in x.fks]):
            yield '''{name}_{name2} = IRelationship(lambda:{clsName}, secondary=lambda:{tieName})'''.format(
                name=re.sub('^[A-Z]*_', '', [name for t,ref,name in x.fks if t==table][0]),
                name2 =re.sub('^[A-Z]*_', '', [t for t,ref,name in x.fks if t!=table][0]),
                clsName=get_class_name([t for t,ref,name in x.fks if t!=table][0]),
                tieName=x.name,
            )

def get_tables_text(Tables, Ties, localized_tables):
    for table in Tables:
        if table.name in ('US_user', 'RO_role'):
            continue
        pk_cols=[
            '    {name} = IColumn({sqlatype}, primary_key=True)'.format(
                name=pkcol.name,
                sqlatype=sqla_types[pkcol.type],
            )
            for pkcol in table.pk
        ]

        columns_text = ['    '+format_col(localized_tables,x) for x in table.attributes]

        yield '''
class {clsName}(Base, db.Model, API, MetadataMixin{localized}):
    __tablename__ = '{loc_prefix}l_{table}'
    valid_time = db.Column({valid_type})
{pk_cols}
{columns}
{ties}
'''.format(
    pk_cols='\n'.join(pk_cols),
    localized=', Localized' if table.localized else '',
    loc_prefix='loc_' if table.localized else '',
    table=table.name,
    clsName=get_class_name(table.name),
    columns='\n'.join(columns_text),
    ties = '\n'.join('    '+x for x in get_table_ties(Ties, table.name)),
    valid_type = sqla_types[table.valid_type],
)


def main(Tables, Enums, Ties):
    print Prefix_text
    localized_tables = [t.name for t in Tables if t.localized]
    print u'\n'.join(get_tables_text(Tables, Ties, localized_tables))
    print u'\n'.join(get_enums_text(Enums))
    print u'\n'.join(get_ties_text(Ties, localized_tables))
