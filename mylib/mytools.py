import sqlite3

def copy_table(cp_from: str, cp_to: str, table: str):
    std_db = sqlite3.connect(cp_from)
    stdlist = std_db.cursor().execute(f'SELECT * FROM {table};')
    db = sqlite3.connect(cp_to)
    cursor = db.cursor()

    if list(cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")) == []:
        cursor.execute(
                f'''CREATE TABLE if NOT EXISTS {table} (
                id      int NOT NULL,
                grp     int(6),
                name    varchar(80),
                PRIMARY KEY (id)
                );'''
        )
        for student in stdlist:
            student = list(student)
            student[2] = student[2].lower()
            cursor.execute(
                f'''INSERT INTO {table} (id, grp, name)
                VALUES ({'"'+'", "'.join(map(str, student)) + '"'});'''
            )

        db.commit()

    db.close()
    std_db.close()
    