PRAGMA foreign_keys = ON;

create table if not exists users (
  id              integer primary key autoincrement,
  email           text not null unique,
  password_hash   text not null,
  status          integer not null default 1,
  created_at      text default current_timestamp
);

create table if not exists run (
  id              integer primary key autoincrement,
  user_id         integer not null,
  van_number      integer not null,
  van_name        text    not null,
  start_time      text    not null,
  first_break     text    not null,
  second_break    text    not null,
  end_time        text,
  number_of_drops integer not null,
  foreign key(user_id) references users(id) on delete cascade
);

create index if not exists idx_run_user_id on run(user_id);

create table if not exists deliveries (
  id        integer primary key autoincrement,
  run_id    integer not null,
  drop_idx  integer not null,
  start_ts  text,
  end_ts    text,
  elapsed   integer,
  expected_minutes real,
  status    text,
  foreign key (run_id) references run(id) on delete cascade,
  unique (run_id, drop_idx)
);

create index if not exists idx_deliveries_run_id on deliveries(run_id);

create table if not exists breaks (
  id              integer primary key autoincrement,
  run_id          integer not null,
  break_number    integer not null,
  scheduled_time  text    not null,
  actual_time     text,
  late_minutes integer,
  status text,
  foreign key (run_id) references run(id) on delete cascade,
  unique (run_id, break_number)
);

create index if not exists idx_breaks_run_id on breaks(run_id);


