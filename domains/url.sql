-- URLs don't have length limits in theory (W3C) but in practice lots
-- of things constrain URL lengths to 2000..8000 characters.
create domain url as varchar check (length(value) <= 8000);

-- create domain url as varchar (value ~ '^[a-z]+://' and length(value) <= 8000);
