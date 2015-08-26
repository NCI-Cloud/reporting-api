from datetime import datetime
from MySQLdb import cursors, escape_string

class DBQueries(object):

    @classmethod
    def _get_tables_comments(cls, dbconn, dbname, table_names):
        query = "SELECT table_comment FROM information_schema.tables WHERE table_schema=%s AND table_name IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
        parameters = [ dbname ]
        parameters.extend(table_names)
        return [ row[0] for row in dbconn.execute(query, cursors.Cursor, parameters).fetchall() ]

    @classmethod
    def _get_table_comment(cls, dbconn, dbname, table_name):
        return cls._get_tables_comments(dbconn, dbname, [ table_name ])[0]

    @classmethod
    def _get_table_lastupdates(cls, dbconn, table_names):
        query = "SELECT ts FROM metadata WHERE table_name IN (" + ",".join([ '%s' ] * len(table_names)) + ");"
        cursor = dbconn.execute(query, cursors.Cursor, table_names)
        return [ row[0] for row in cursor.fetchall() ]

    @classmethod
    def _get_table_lastupdate(cls, dbconn, table_name):
        rows = cls._get_table_lastupdates(dbconn, [ table_name ])
        if rows:
            return rows[0]
        return datetime.utcfromtimestamp(0).isoformat()

    @classmethod
    def _get_table_list(cls, dbconn):
        query = 'SHOW TABLES;'
        cursor = dbconn.execute(query, cursors.Cursor)
        return [ row[0] for row in cursor.fetchall() ]

    @classmethod
    def _update_table(cls, dbconn, table_name):
        try:
            cursor = dbconn.callproc(escape_string(table_name + '_update'), cursors.DictCursor)
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
        cursor = dbconn.execute(query, cursors.DictCursor, parameters)
        return [ cursor.fetchall() ]
