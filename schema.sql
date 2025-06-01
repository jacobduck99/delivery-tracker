CREATE TABLE IF NOT EXISTS run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    van_number INTEGER NOT NULL,
    van_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    first_break TEXT NOT NULL,
    second_break TEXT NOT NULL,
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
    FOREIGN KEY (run_id) REFERENCES run(id)
);
