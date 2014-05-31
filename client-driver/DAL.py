# Author : Rajat Khanduja
# Date : 31 May 2014

import sqlite3

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class DAL:

    DB_FILE = 'allmyspace.db'
    FILE_MAPPINGS_TABLE = 'file_mappings'

    def __init__(self):
        self.connection = sqlite3.connect(self.DB_FILE, isolation_level=None)
        self.connection.row_factory = dict_factory
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS " + self.FILE_MAPPINGS_TABLE + "(" +
                       "    local_path TEXT, " +
                       "    remote_path TEXT, " +
                       "    provider TEXT, " +
                       "    is_shared INTEGER, " +
                       "    share_link TEXT)")
        cursor.close()

    def add_file(self, local_path, remote_path, provider, is_shared = 0, share_link = None):
        cursor = self.connection.cursor()
        insert_query = "INSERT INTO " + self.FILE_MAPPINGS_TABLE +\
                       "(local_path, remote_path, provider, is_shared, share_link)" +\
                       "VALUES(?, ? , ?, ?, ?)"
        cursor.execute(insert_query, (local_path, remote_path, provider, is_shared, share_link))
        cursor.close()

    def update_share_status(self, local_path, is_shared, share_link):
        cursor = self.connection.cursor()
        update_query = "UPDATE " + self.FILE_MAPPINGS_TABLE +\
                       " SET is_shared = ?, share_link = ?" +\
                       " WHERE local_path = ?"
        cursor.execute(update_query, (is_shared, share_link, local_path))
        cursor.close()

    def get_file_mappings(self, local_path):
        cursor = self.connection.cursor()
        query = ("SELECT local_path, remote_path, is_shared, share_link FROM " + self.FILE_MAPPINGS_TABLE +
                 " WHERE local_path = '{}'").format(local_path)
        cursor.execute(query)
        row = cursor.fetchone()
        return row
