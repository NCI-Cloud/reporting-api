from datetime import datetime
from MySQLdb import escape_string
from common.dbconn import ResultSet, ResultSetSlice

class DBQueries(object):

    @classmethod
    def _get_tables_comments(cls, dbconn, dbname, table_names):
        query = "SELECT table_comment FROM information_schema.tables WHERE table_schema=%s AND table_name IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
        parameters = [ dbname ]
        parameters.extend(table_names)
        cursor = dbconn.execute(query, False, parameters)
        return ResultSetSlice(cursor, 0)

    @classmethod
    def _get_table_comment(cls, dbconn, dbname, table_name):
        comments = cls._get_tables_comments(dbconn, dbname, [ table_name ])
        return iter(comments).next()

    @classmethod
    def _get_table_lastupdates(cls, dbconn, table_names):
        query = "SELECT last_update FROM metadata WHERE table_name IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
        cursor = dbconn.execute(query, False, table_names)
        return ResultSetSlice(cursor, 0)

    @classmethod
    def _get_table_lastupdate(cls, dbconn, table_name):
        rows = cls._get_table_lastupdates(dbconn, [ table_name ])
        try:
            row = iter(rows).next()
        except StopIteration:
            row = datetime.utcfromtimestamp(0).isoformat()
        return row

    @classmethod
    def _get_table_list(cls, dbconn):
        query = 'SHOW TABLES;'
        cursor = dbconn.execute(query, False)
        return ResultSetSlice(cursor, 0)

    @classmethod
    def _update_table(cls, dbconn, table_name):
        try:
            cursor = dbconn.callproc(escape_string(table_name + '_update'), True)
            cursor.fetchall()
        except:
            # Can't refresh the report. Degrade gracefully by serving old data.
            pass

    @classmethod
    def _filter_table(cls, dbconn, table_name, filter_args):
        DBQueries._update_table(dbconn, table_name)
        query = 'SELECT * FROM ' + escape_string(table_name)
        parameters = []
        if filter_args:
            query += ' WHERE '
            criteria = []
            for (key, val) in filter_args.items():
                criteria.append(escape_string(key) + "=%s")
                parameters.append(val[0])
            query += ' AND '.join(criteria)
        else:
            # TODO: Add an Expires header and respond to conditional GETs
            # headers.append(('Expires', ))
            pass
        query += ';'
        cursor = dbconn.execute(query, True, parameters)
        return ResultSet(cursor)
