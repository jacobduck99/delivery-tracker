CREATE TABLE IF NOT EXISTS run (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  van_number      INTEGER NOT NULL,
  van_name        TEXT    NOT NULL,
  start_time      TEXT    NOT NULL,
  first_break     TEXT    NOT NULL,
  second_break    TEXT    NOT NULL,
  end_time        TEXT,
  number_of_drops INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS deliveries (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id    INTEGER NOT NULL,
  drop_idx  INTEGER NOT NULL,
  start_ts  TEXT,
  end_ts    TEXT,
  elapsed   INTEGER,
  FOREIGN KEY (run_id) REFERENCES run(id)
);

CREATE TABLE IF NOT EXISTS breaks (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id          INTEGER NOT NULL,
  break_number    INTEGER NOT NULL,
  scheduled_time  TEXT    NOT NULL,
  actual_time     TEXT,
  late_minutes INTEGER,
  status TEXT,
  FOREIGN KEY (run_id) REFERENCES run(id),
  UNIQUE (run_id, break_number)
);
