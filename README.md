# modeler
(Bi-temporal) data modelling tool inspired by Anchor modeler, for PostgreSQL

This is a tool I wrote a while ago for some fancy (bi-)temporal DB modelling with PostgreSQL.
Inspired by [Anchormodeler](https://github.com/Roenbaeck/anchor), which was MS SQL -only at the time of writing.

NB. This is an exploratory project in DB modelling, not for production use, etc. etc.

## Principles:
- Aim for a maximally normalized data model (i.e., 6NF)
- Use DB constraints to the fullest extent feasible

## Features:
- Temporal 6NF database support with a notion of "validity time" AND
  transaction time
- Support for individual localized fields
- Uses PostgreSQL specific features to the fullest extent: domains,
  table inheritance, extensions, etc.
- Doesn't get in the way (hopefully): When something is easier to
  define in SQL directly, allows doing that
- Temporal and non-temporal enums (with optionally localized
  values). Although PostgreSQL also has Enum types, we don't use them
  here since they have more overhead (4 bytes) and it's easier to work
  with integers directly when working with other languages.


## Missing:
- A mechanism for all types of schema updates. Outright conflicts with
  previous schema versions make it difficult to
- Composite primary key support in some cases


# Usage:
1. Define a schema in a YAML file (no examples provided as of now)
2. Create a PostgreSQL database with the btree_gist extension, ensuring it is UTF-8.
3. Execute modeler for any relevant output modes (e.g. sql, flask):
   python modeler.py sql < model.yaml > db.sql
   python modeler.py flask < model.yaml > flask_model.py


# Inner workings
- Generated SQL can be executed without side-effects multiple times (i.e., the generated SQL is idempotent)
- Possible schema incompatibilities (relatively rare) must be resolved with another mechanism.
- GIST indexes are used to enforce temporal consistency
