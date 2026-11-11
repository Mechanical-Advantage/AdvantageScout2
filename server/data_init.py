import json
import sqlite3
import os
from config import config

error_list = []

MODE_BASE_COLUMNS = {
    "match": "Device TEXT, Team INTEGER, Alliance TEXT, Scout TEXT, Match INTEGER, Event TEXT",
    "pit": "Device TEXT, Team INTEGER, Scout TEXT, Event TEXT",
    "super": "Device TEXT, Team1 INTEGER, Team2 INTEGER, Team3 INTEGER, Alliance TEXT, Scout TEXT, Event TEXT",
}


def pascal_case(text: str):
    return "".join(word[:1].upper() + word[1:] for word in text.split())


def error(message: str):
    error_list.append(message)
    print(message + "!")


def show_errors():
    formatted = "\n".join(error_list)
    raise Exception(
        f"\nThe operation could not be completed, the following errors occured:\n{formatted}"
    )


def sql_literal(field_type: str, default):
    if field_type == "TEXT":
        return "'" + str(default).replace("'", "''") + "'"
    if field_type == "BOOLEAN":
        return "TRUE" if default else "FALSE"
    return str(default)


def compile_node(node: dict, prefix: str, mode: str, fields: dict, sql_columns: list):
    for field in node.get("fields", []):
        name = field.get("name")
        if not name:
            error(f"{mode}: a field under '{prefix}' is missing a name")
            continue
        field_name = prefix + name
        field["name"] = field_name

        field_type = field.get("type", "").upper()
        default = field.get("default")

        if field_type in ("INTEGER", "NUMERIC"):
            if field.get("min") is None:
                field["min"] = default if default is not None else 0
            if default is None:
                default = 0
                field["default"] = default
        elif field_type == "TEXT":
            if field.get("min") is None:
                field["min"] = 0
            elif field["min"] < 0:
                error(
                    f"{mode}: field {field_name} has an invalid minimum string length"
                )
            if default is None:
                default = ""
                field["default"] = default
        elif field_type == "BOOLEAN":
            default = bool(default)
            field["default"] = default
        else:
            error(f"{mode}: type '{field.get('type')}' of {field_name} is not valid")
            continue

        if field_name in fields:
            error(f"{mode}: duplicate field detected: {field_name}")

        fields[field_name] = default

        sql_columns.append(
            f"{field_name} {field_type} DEFAULT {sql_literal(field_type, default)}"
        )

    for key, child in node.items():
        if key == "fields" or not isinstance(child, dict):
            continue
        compile_node(child, prefix + pascal_case(key), mode, fields, sql_columns)


def compile_game_json(mode: str):
    error_list.clear()
    json_path = getattr(config, f"{mode.upper()}_JSON_PATH")
    with open(json_path, "r") as json_file:
        raw = json.load(json_file)

    fields = {}
    sql_columns = []

    for section_key, section in raw.items():
        compile_node(section, pascal_case(section_key), mode, fields, sql_columns)

    if error_list:
        show_errors()

    compiled = {
        "fields": fields,
        "setup": raw,
    }
    return compiled, sql_columns


def create_database(mode: str, sql_columns, delete_db: bool):
    db_path = getattr(config, f"{mode.upper()}_DB_PATH")
    table = getattr(config, f"{mode.upper()}_TABLE")

    if delete_db:
        try:
            os.remove(db_path)
            print(f"Removed {mode} database")
        except FileNotFoundError:
            print(f"No {mode} database to remove")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({MODE_BASE_COLUMNS[mode]})")

    print(f"Adding fields to {mode} database...")
    # CREATE TABLE IF NOT EXISTS is a no-op on an already-existing table, so
    # a base column added to MODE_BASE_COLUMNS after a database was first
    # created (e.g. Event) would never actually reach it without also
    # ALTER-ing it in here, same as the JSON-driven columns below.
    base_columns = [col.strip() for col in MODE_BASE_COLUMNS[mode].split(",")]
    for column_sql in base_columns + sql_columns:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_sql}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()
    print(f"Updated {mode} database successfully")


def init_mode(mode: str, delete_db: bool):
    compiled, sql_columns = compile_game_json(mode)
    create_database(mode, sql_columns, delete_db)
    return compiled


def init_database_fields(delete_db=False):
    return {mode: init_mode(mode, delete_db) for mode in ("match", "pit", "super")}


if __name__ == "__main__":
    print(init_database_fields(True))
