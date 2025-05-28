DROP TABLE IF EXISTS run ;

CREATE TABLE run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    van_number INTEGER,
    start_time TEXT NOT NULL,
    end_time TEXT,
    number_of_drops INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS deliveries (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id    INTEGER,            
  drop_idx  INTEGER,            
  start_ts  TEXT,
  end_ts    TEXT,
  elapsed   INTEGER,           
  FOREIGN KEY(run_id) REFERENCES runs(id)
);

