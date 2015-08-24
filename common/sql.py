import re

class SQL(object):
    '''
    Contains methods relating to SQl databases.
    '''

    def __init__(self, params):
        '''
        Constructor
        '''

    @classmethod
    def _safe_identifier(cls, string):
        """
        FIXME: How to defend against SQL injection?
        The test below is primitive but effective.
        PyMySQLdb has no placeholders for table names :-(
        """
        if re.compile('^[a-zA-Z0-9_]*$').match(string):
            return True
        return False
