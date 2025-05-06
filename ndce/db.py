import sqlite3


DB_NAME = 'ndce.db'


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
            if self.db_commit:
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
