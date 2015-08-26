import MySQLdb
from _mysql_exceptions import OperationalError

class DBConnection(object):
    '''
    Represents a connection to an RDBMS.
    '''

    def __init__(self, **kwargs):
        self.conn = MySQLdb.connect(**kwargs)

    def _before_db(self):
        """
        MySQL-specific: attempt to reconnect if our connection has timed out
        """
        try:
            self.conn.ping(True)
        except OperationalError:
            """
            Probably just a stale connection.
            If something worse has gone wrong, we will see it soon anyway.
            """
            pass

    def execute(self, query, cursor_class, bind_values = None):
        """
        Execute the given query with the given values for placeholders.
        Return a cursor of the given class.
        """
        self._before_db()
        cursor = self.conn.cursor(cursor_class)
        cursor.execute(query, bind_values)
        return cursor

    def callproc(self, procname, cursor_class, args = []):
        """
        Execute the given-named stored procedure with the given arguments.
        Return a cursor of the given class.
        """
        self._before_db()
        cursor = self.conn.cursor(cursor_class)
        cursor.callproc(procname, args)
        return cursor
