create domain language_code as char check (length(value) = 2 and value = lower(value));
