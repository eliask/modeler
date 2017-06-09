-- Regular, weekly opening hours specification.
-- Implemented with tstzrange.
-- One row per one continuous set of opening times/hours.
-- Somewhat related to https://schema.org/openingHours
-- TODO: put into another schema or something.

create domain business_opening_hours as tstzrange CHECK (
lower_inc(value) AND upper_inc(value)
);

create domain business_opening_hours_regular as business_opening_hours CHECK (
-- Note: 2007-01-01 is conveniently Monday
value <@ '[2007-01-01 00:00+0, 2007-01-08 00:00+0]'::tstzrange
);
