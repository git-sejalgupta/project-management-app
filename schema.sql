CREATE TABLE IF NOT EXISTS projects (
	"id"	INTEGER NOT NULL UNIQUE,
	"code"	TEXT NOT NULL UNIQUE,
	"archived"	INTEGER NOT NULL DEFAULT 0,
	"start_date"	TEXT,
	"end_date"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
) STRICT;

CREATE TABLE IF NOT EXISTS software (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	"version"	TEXT NOT NULL,
	"vendor"	TEXT,
	"deprecated"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("name","version")
);

CREATE TABLE IF NOT EXISTS project_software (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    software_id INTEGER NOT NULL,
    UNIQUE (project_id, software_id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (software_id) REFERENCES software(id)
);
