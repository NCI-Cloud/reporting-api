"""
Represents a connection to an RDBMS.
"""

import mysql.connector
from mysql.connector import InterfaceError


class DBConnection(object):
    """
    Represents a connection to an RDBMS.
    """

    def __init__(self, **kwargs):
        """
        MySQL stores TIMESTAMP values as UTC, but automatically converts them
        to/from the 'current time zone' on output/input (respectively).
        By default, the 'current time zone' is the server's time zone,
        which is unknown to the client. Thus this is silent data corruption.
        There is no way to disable this conversion, so defeat it by setting
        the 'current time zone' to UTC upon connection.
        """
        if 'time_zone' not in kwargs:
            kwargs['time_zone'] = '+00:00'
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

    def execute(self, query, return_dictionaries=True, bind_values=None):
        """
        Execute the given query with the given values for placeholders.
        If return_dictionaries is true, each row is a dictionary;
        if it is false, each row is a list of column values.
        In either case, a resultset is a list of rows.
        """
        cursor = self.conn.cursor(
            dictionary=return_dictionaries, buffered=False
        )
        # Make this a strong not a weak reference, to prevent premature GC.
        # Works around change:
        # http://bazaar.launchpad.net/~mysql/myconnpy/1.0/revision/201
        cursor._connection = self.conn
        cursor.execute(query, bind_values)
        return cursor

    def callproc(self, procname, return_dictionaries=True, args=()):
        """
        Execute the given-named stored procedure with the given arguments.
        If return_dictionaries is true, each row is a dictionary;
        if it is false, each row is a list of column values.
        In either case, a resultset is a list of rows.
        """
        cursor = self.conn.cursor(
            dictionary=return_dictionaries, buffered=False
        )
        cursor.callproc(procname, args)
        return cursor


# Pylint warns that the following class has too few public methods.
# The class has the sole public method that it is intended to have,
# so the following comment disables the warning.
# pylint: disable=R0903

class CursorIter(object):

    """
    Iterate over a cursor's emitted rows.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def next(self):
        """
        Return the next row yielded by this cursor.
        Raise StopIteration if the cursor is exhausted,
        ie all of its rows have already been read.
        """
        row = self.cursor.fetchone()
        if row is None:
            raise StopIteration()
        return row


class CursorSliceIter(CursorIter):

    """
    Iterate over a slice of a cursor's emitted rows,
    so that the n'th column of each row is emitted.
    """

    def __init__(self, cursor, index):
        super(CursorSliceIter, self).__init__(cursor)
        self.index = index

    def next(self):
        """
        Return one column of the next row yielded by this cursor.
        Raise StopIteration if the cursor is exhausted,
        ie all of its rows have already been read.
        """
        row = super(CursorSliceIter, self).next()
        return row[self.index]


# Pylint warns that the following class has too few public methods.
# It is not intended to have many (or even any) public methods,
# so this is not a problem, so the following comment silences the warning.
# Apparently, pylint assumes (falsely) that a class without public methods
# is being abused as a mere holder of data - but the below class is being
# used as a holder of code, as is common accepted practice in OOP.
# pylint: disable=R0903

class ResultSet(object):

    """
    An iterable SQL result set.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def __iter__(self):
        return CursorIter(self.cursor)


# Pylint warns that the following classes have too few public methods.
# They are not intended to have many (or even any) public methods,
# so this is not a problem, so the following comment silences the warning.
# Apparently, pylint assumes (falsely) that a class without public methods
# is being abused as a mere holder of data - but the below classes are being
# used as holders of code, as is common accepted practice in OOP.
# pylint: disable=R0903

class ResultSetSlice(ResultSet):

    """
    An iterable slice through an SQL result set.
    """

    def __init__(self, cursor, index):
        super(ResultSetSlice, self).__init__(cursor)
        self.index = index

    def __iter__(self):
        return CursorSliceIter(self.cursor, self.index)
