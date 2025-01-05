import sqlite3
from typing import List


class SQLiteDB:
    def __init__(self, db_name):
        """
        Initialize the SQLiteDB class with the database name.
        """
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.open_connection()

    def open_connection(self):
        """
        Open a connection to the SQLite database.
        """
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
            print(f"Connection to {self.db_name} is open.")
        else:
            print("Connection is already open.")

    def execute_query(self, query, params=None):
        """
        Execute a SQL query.
        :param query: The SQL query to execute.
        :param params: Optional parameters for the query.
        """
        if self.connection:
            try:
                if params:
                    self.cursor.executemany(query, params)
                else:
                    self.cursor.execute(query)
                self.connection.commit()
                print("Query executed successfully.")
            except sqlite3.Error as e:
                print(f"An error occurred: {e}")
        else:
            print("No open connection to execute the query.")

    def fetch_all(self, query, params=None) -> List:
        """
        Execute a SELECT query and fetch all results.
        :param query: The SELECT query to execute.
        :param params: Optional parameters for the query.
        :return: Fetched results.
        """
        if self.connection:
            try:
                if params:
                    self.cursor.executemany(query, params)
                else:
                    self.cursor.execute(query)

                rows = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]
                result = [dict(zip(columns, row)) for row in rows]        # turning data into list of key-value pairs
                return result

            except sqlite3.Error as e:
                print(f"An error occurred: {e}")
                return None
        else:
            print("No open connection to fetch results.")
            return None

    def close_connection(self):
        """
        Close the SQLite database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            print("Connection to the database has been closed.")
        else:
            print("Connection is already closed.")
