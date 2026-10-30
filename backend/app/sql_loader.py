"""Executes MySQL script files that use the mysql-CLI `DELIMITER` directive (procedures/triggers)."""
from pathlib import Path


def split_sql(script: str):
    statements, buffer, delimiter = [], [], ";"
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split()[1]
            continue
        if not buffer and (not stripped or stripped.startswith("--")):
            continue
        buffer.append(line)
        if stripped.endswith(delimiter):
            statement = "\n".join(buffer).rstrip()[: -len(delimiter)].strip()
            if statement:
                statements.append(statement)
            buffer = []
    return statements


def apply_sql_file(connection, path: Path):
    # Raw DB-API cursor: avoids driver %-formatting of literal '%' characters in SQL bodies.
    cursor = connection.connection.cursor()
    try:
        for statement in split_sql(path.read_text(encoding="utf-8")):
            cursor.execute(statement)
    finally:
        cursor.close()
