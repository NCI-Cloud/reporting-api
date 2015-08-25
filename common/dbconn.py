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

    def execute(self, query, cursor_class):
        self._before_db()
        cursor = self.conn.cursor(cursor_class)
        cursor.execute(query)
        return cursor
