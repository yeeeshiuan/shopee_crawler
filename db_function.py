import sqlite3
from pathlib import Path

database_dir_name = 'database'
databasae_file_name = 'example.db'

def create_tables(cur):
    # Create table
    try:
        cur.execute('''CREATE TABLE product 
                       (description text, price text)''')
    except:
        return False
    else:
        return True

def re_create_tables(cur):
    # Drop and then Create table
    try:
        cur.execute('''DROP TABLE product''')
        cur.execute('''CREATE TABLE product 
                        (description text, price text)''')
    except:
        return False
    else:
        return True


def init_database():
    Path(f"{database_dir_name}").mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f"{database_dir_name}/{databasae_file_name}")
    cur = con.cursor()

    if not create_tables(cur):
        re_create_tables(cur)

    con.close()
