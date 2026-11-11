import json
import sqlite3

def insert_data(data, db_path, table):
    if not data:
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        batches = {}
        for item in data:
            keys_tuple = tuple(item.keys())
            
            processed_values = [
                json.dumps(v) if isinstance(v, (dict, list)) else v 
                for v in item.values()
            ]
            
            if keys_tuple not in batches:
                batches[keys_tuple] = []
            batches[keys_tuple].append(tuple(processed_values))

        for keys_tuple, rows in batches.items():
            keys_str = ', '.join(keys_tuple)
            placeholders = ', '.join(['?'] * len(keys_tuple))
            
            sql = f"INSERT INTO {table} ({keys_str}) VALUES ({placeholders})"
            cur.executemany(sql, rows)

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database insertion failed: {e}")
        raise e
    finally:
        conn.close()

def update_data(data, db_path, table, conflict_col, target_column=None):
    if not data:
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for item in data:
        processed_values = [
            json.dumps(v) if isinstance(v, (dict, list)) else v 
            for v in item.values()
        ]
        
        keys = list(item.keys())
        placeholders = ', '.join(['?'] * len(keys))
        columns_str = ', '.join(keys)

        if target_column:
            update_action = f"{target_column} = excluded.{target_column}"
        else:
            update_pairs = [f"{k} = excluded.{k}" for k in keys if k != conflict_col]
            update_action = ', '.join(update_pairs)

        sql = f"""
        INSERT INTO {table} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT({conflict_col}) DO UPDATE SET
        {update_action}
        """

        cur.execute(sql, tuple(processed_values))

    conn.commit()
    conn.close()