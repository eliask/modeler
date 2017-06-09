-- Non-negative integer domains:

create domain nonneg16 as smallint check (value >= 0);
create domain nonneg32 as integer check (value >= 0);
create domain nonneg64 as bigint check (value >= 0);

create domain nonneg_smallint as smallint check (value >= 0);
create domain nonneg_integer as integer check (value >= 0);
create domain nonneg_bigint as bigint check (value >= 0);

-- Positive integer domains:

create domain positive16 as smallint check (value > 0);
create domain positive32 as integer check (value > 0);
create domain positive64 as bigint check (value > 0);

create domain pos_smallint as smallint check (value > 0);
create domain pos_integer as integer check (value > 0);
create domain pos_bigint as bigint check (value > 0);
