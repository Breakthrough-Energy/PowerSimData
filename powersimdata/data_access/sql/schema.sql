CREATE DATABASE psd;
\connect psd;
CREATE TABLE IF NOT EXISTS execute_list(
  id int primary key not null,
  status text not null
);
CREATE TABLE IF NOT EXISTS scenario_list(
  id int primary key not null,
  plan text not null,
  name text not null,
  state text not null,
  interconnect text not null,
  base_demand text not null,
  base_hydro text not null,
  base_solar text not null,
  base_wind text not null,
  change_table boolean not null,
  start_date timestamptz not null,
  end_date timestamptz not null,
  interval text not null,
  engine text not null,
  runtime text,
  infeasibilities text
);
