import sqlite3
from config import DB_NAME


class UseDatabase:
    
    def __init__(
        self, db_name: str = DB_NAME, db_commit: bool = False
    ) -> None:
        self.db_name = db_name
        self.db_commit = db_commit
        
    def __enter__(self) -> None:
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            return self.cursor
        except Exception as e:
            print(e)

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        try:
            print()
            #if self.db_commit:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()
        except Exception as e:
            print(e)


def make_db_request(sql_query: str) -> None:
    with UseDatabase() as cursor:
        try:
            cursor.execute(sql_query)
            return cursor.fetchall()
        except Exception as e:
            print(e)


def db_request(sql_query: str, row: tuple[str]) -> None:
    with UseDatabase() as cursor:
        print(sql_query, row)
        try:
            cursor.execute(sql_query, row)
            return cursor.fetchall()
        except Exception as e:
            print(e)


def update_db(result: dict):    
    for i in result:
        row = (('vendor', i['vendor'], i['host']),('model', i["model"], i['host']),('category', i['category'], i['host']))
        for data in row:
            sql_query_update = f'UPDATE Device set {data[0]} = ? WHERE host = ?'
            db_request(sql_query_update, data[1:])


def insert_db(result: dict):
    sql_query_add = 'INSERT into Device values (?, ?, ?, ?)'
    for i in result:
        row = (str(i['vendor']), str(i['model']), str(i['category']), str(i['host']))
        db_request(sql_query_add, row)


def del_db_data(result):
    sql_query_del ='DELETE FROM Device WHERE host=?'
    for i in result:
        db_request(sql_query_del, (i, ))

def get_all_rows():
    sql_query='SELECT * FROM Device'
    return make_db_request(sql_query)

def get_row(row):
    sql_query= f'SELECT * from Device where {row[0]} = {row[1]}'
    return make_db_request(sql_query)

