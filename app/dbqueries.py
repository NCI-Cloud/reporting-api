from datetime import datetime
from MySQLdb import escape_string
from common.dbconn import ResultSet, ResultSetSlice

class DBQueries(object):

    """
    Holds a set of canned database queries.
    """

    UPDATE_PROC_SUFFIX = '_update'
    QUERY_SHOW_TABLES = 'SHOW TABLES;'
    METADATA_TABLE = 'metadata'
    METADATA_LAST_UPDATE_COLUMN = 'last_update'
    METADATA_TABLE_NAME_COLUMN = 'table_name'

    @classmethod
    def _get_tables_comments(cls, dbconn, dbname, table_names):
        """
        Return an iterator over the SQL92 table comments for the given tables.
        """
        # In this query, schema and table names are literals, so can be parameters
        query = "SELECT table_comment FROM information_schema.tables WHERE table_schema=%s AND table_name IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
        parameters = [ dbname ]
        parameters.extend(table_names)
        cursor = dbconn.execute(query, False, parameters)
        return ResultSetSlice(cursor, 0)

    @classmethod
    def _get_table_comment(cls, dbconn, dbname, table_name):
        """
        Obtain a single table's SQL92 table comment.
        """
        comments = cls._get_tables_comments(dbconn, dbname, [ table_name ])
        return iter(comments).next()

    @classmethod
    def _get_table_lastupdates(cls, dbconn, table_names):
        """
        Return an iterator over the last update times for the given tables.
        This is looked for in an optional table named 'metadata'.
        FIXME: Remove this knowledge about the underlying schema.
        """
        # In this query, table names are literals, so can be parameters
        query = "SELECT " + escape_string(cls.METADATA_LAST_UPDATE_COLUMN) + " FROM " + escape_string(cls.METADATA_TABLE) + " WHERE " + escape_string(cls.METADATA_TABLE_NAME_COLUMN) + " IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
        cursor = dbconn.execute(query, False, table_names)
        return ResultSetSlice(cursor, 0)

    @classmethod
    def _get_table_lastupdate(cls, dbconn, table_name):
        """
        Obtain a single table's last update time.
        """
        rows = cls._get_table_lastupdates(dbconn, [ table_name ])
        try:
            row = iter(rows).next()
        except StopIteration:
            row = datetime.utcfromtimestamp(0)
        return row

    @classmethod
    def _get_table_list(cls, dbconn):
        """
        Return an iterator over names of available tables.
        """
        query = cls.QUERY_SHOW_TABLES
        cursor = dbconn.execute(query, False)
        return ResultSetSlice(cursor, 0)

    @classmethod
    def _make_update_proc_name(cls, table_name):
        # FIXME: Remove this knowledge about the underlying schema.
        return table_name + cls.UPDATE_PROC_SUFFIX

    @classmethod
    def _update_table(cls, dbconn, table_name):
        """
        Call a stored procedure to update the given-named table.
        """
        try:
            # Stored procedure names cannot be parameters, so must be escaped
            cursor = dbconn.callproc(escape_string(cls._make_update_proc_name(table_name)), True)
            cursor.fetchall()
        except:
            # Can't refresh the report. Degrade gracefully by serving old data.
            pass

    @classmethod
    def _filter_table(cls, dbconn, table_name, filter_args):
        """
        Return an iterator over the records in a resultset
        selecting all columns from the given-named table.
        The filter_args are ANDed together then used as a WHERE criterion.
        """
        DBQueries._update_table(dbconn, table_name)
        # Table names cannot be parameters, so must be escaped
        query = 'SELECT * FROM ' + escape_string(table_name)
        parameters = []
        if filter_args:
            query += ' WHERE '
            criteria = []
            for (key, val) in filter_args.items():
                # Column names cannot be parameters, so must escaped
                criteria.append(escape_string(key) + "=%s")
                # Filter values can be parameters
                parameters.append(val[0])
            query += ' AND '.join(criteria)
        query += ';'
        cursor = dbconn.execute(query, True, parameters)
        return ResultSet(cursor)
