import mysql.connector
from mysql.connector import InterfaceError

class DBConnection(object):
    '''
    Represents a connection to an RDBMS.
    '''

    def __init__(self, **kwargs):
        self.conn = mysql.connector.connect(**kwargs)

    def _before_db(self):
        """
        MySQL-specific: attempt to reconnect if our connection has timed out
        """
        try:
            self.conn.ping(True)
        except InterfaceError:
            """
            Probably just a stale connection.
            If something worse has gone wrong, we will see it soon anyway.
            """
            pass

    def execute(self, query, return_dictionaries = True, bind_values = None):
        """
        Execute the given query with the given values for placeholders.
        If return_dictionaries is true, each row is a dictionary;
        if it is false, each row is a list of column values.
        In either case, a resultset is a list of rows.
        """
        cursor = self.conn.cursor(dictionary = return_dictionaries)
        cursor.execute(query, bind_values)
        return cursor

    def callproc(self, procname, return_dictionaries = True, args = []):
        """
        Execute the given-named stored procedure with the given arguments.
        If return_dictionaries is true, each row is a dictionary;
        if it is false, each row is a list of column values.
        In either case, a resultset is a list of rows.
        """
        cursor = self.conn.cursor(dictionary = return_dictionaries)
        cursor.callproc(procname, args)
        return cursor
