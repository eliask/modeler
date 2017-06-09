-- Half-open ranges to make temporal stuff more manageable.
--
-- The first NULL check is to make it easier to deal with these values
-- in triggers and such.  The NOT NULL constraint is enforced in the
-- table structure anyway.
--
create domain tstzrange_half_open as tstzrange CHECK (
  value IS NULL OR (
    lower(value) IS NOT NULL
    AND upper(value) IS NOT NULL
    AND lower_inc(value)
    AND not upper_inc(value)
  )
);
create domain daterange_half_open as daterange CHECK (
  value IS NULL OR (
    lower(value) IS NOT NULL
    AND upper(value) IS NOT NULL
    AND lower_inc(value)
    AND not upper_inc(value)
  )
);
