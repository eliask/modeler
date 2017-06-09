create table if not exists transaction_valid_tstzrange (
  transaction_time tstzrange_half_open not null
  default tstzrange(current_timestamp, 'infinity', '[)')
  ,
  valid_time tstzrange_half_open not null
  default tstzrange(current_timestamp, 'infinity', '[)')
);

create table if not exists transaction_valid_daterange (
  transaction_time tstzrange_half_open not null
  default tstzrange(current_timestamp, 'infinity', '[)')
  ,
  valid_time daterange_half_open not null
  default daterange(current_date, 'infinity', '[)')
);


create type "RoleType" as ENUM ('OrganizationUser', 'OrganizationAdmin', 'SuperAdmin');

create table language_iso639 (
  code char(2) primary key -- ISO 639-1
  ,code3 char(3) not null -- ISO 639-2/T
  ,CHECK (code=lower(code))
  ,CHECK (code3=lower(code3))
);

create table language_official_name (
  metadata integer not null
  ,language_code char(2) not null references language_iso639(code)
  ,name_code char(2) not null references language_iso639(code)
  ,name varchar not null
  ,EXCLUDE USING gist (
    language_code with =
    ,name_code with =
    ,transaction_time with &&
    ,valid_time with &&
  )
) INHERITS (transaction_valid_daterange);

-- TODO: Too lazy to do this more properly
INSERT INTO language_iso639
select * from
(
select 'en' a,'eng' b
union all select 'zh','zho'
union all select 'fi','fin'
union all select 'ru','rus'
) tmp
where tmp.a not in (select code from language_iso639);


create or replace function point_to_json(location geometry(point)) RETURNS json
AS $$
BEGIN
  RETURN point_to_json(location::point);
END;
$$ LANGUAGE plpgsql;

create or replace function point_to_json(location point) RETURNS json
AS $$
BEGIN
  RETURN ('{"x":'||location[0]||',"y":'||location[1]||'}')::json;
END;
$$ LANGUAGE plpgsql;
