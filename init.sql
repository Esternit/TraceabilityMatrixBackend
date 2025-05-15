CREATE TABLE IF NOT EXISTS json_files (
    id UUID PRIMARY KEY,
    readable_name TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE
);