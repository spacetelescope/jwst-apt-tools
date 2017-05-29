#!/usr/bin/env python

import argparse
import csv
from astropy.table import Table

def arguments():
    """Parse and return command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Show in browser PPSDB table data (.sql) exported by APT.'
                "\nList available tables, if 'table' is not specified.",
        epilog='example: aptx_sql.py 98765.sql exposures')
    parser.add_argument('sqlfile',help='SQL file exported by APT')
    parser.add_argument('tablename',nargs='?',default=None,
            help='Name of a table in the SQL file')
    return parser.parse_args()

class Sqlfile:
    """An sql file exported by APT.
    """

    def __init__(self, sqlfile):
        """Read data from sql file. Get list of tables names.
        """
        self.__sqlfile = sqlfile
        self.__sql = self.sqlread()
        self.tablenames = self.tablenames()

    def sqlread(self):
        """Read sql file exported by APT. Strip trailing newlines.
        """
        sql = list()
        with open(self.__sqlfile, 'r') as f:
            for line in f:
                sql.append(line.rstrip())
        return sql

    def tablenames(self):
        """Parse sql insert statements to determine table names.
        """
        prefix = 'insert into '
        names = list()
        for line in self.__sql:
            if line[:len(prefix)] == prefix:
                names.append(line[len(prefix):line.find('(')].strip())
        names = sorted(list(set(names)))
        names.remove('#AOK values')
        return names

    def rows_from_sql(self, tablename):
        """Return dictionary for each row in the specified table.
        Dictionary keys may differ for each sql insert statement.
        """
        prefix = 'insert into ' + tablename + ' '
        rows = list()
        for line in self.__sql:
            if line[:len(prefix)] == prefix:
                keyval_str = line[len(prefix):].strip()
                keystr, valstr = keyval_str.split('values')
                keys = [k.strip() for k in keystr[2:-2].split(',')]
                vals = [v.strip() for v in valstr[2:-2].split(',')]
                keyval_dict = dict(zip(keys, vals))
                rows.append(keyval_dict)
        return rows

    def keys(self, rows):
        keys = set()
        for row in rows:
            keys = keys.union(row.keys())
        keys = sorted(list(keys))
        return keys

    def cols_from_rows(self, rows, keys):
        table = Table()
        for key in keys:
            col = list()
            for row in rows:
                col.append(row.get(key, ''))
            try:
                col = [int(x) for x in col]
            except ValueError:
                try:
                    col = [float(x) for x in col]
                except ValueError:
                    col = [x[1:-1] if x.startswith("'") and x.endswith("'") \
                            else x for x in col]
            table[key] = col
        return table

    def table(self, tablename, browser=False):
        """Construct astropy table from sql insert statements.
        For the 'exposures' table, discard rows with apt_label == 'BASE'.
        Convert column data type to integer or float, where possible.
        Strip beginning and ending single quote from strings.
        """
        rows = self.rows_from_sql(tablename)
        keys = self.keys(rows)
        if len(keys) == 0:
            raise Exception("no '" + tablename + "' table in " + self.__sqlfile)
        table = self.cols_from_rows(rows, keys)
        if browser:
            self.browser(table)
        return table

    def browser(self, table):
        """Diplay copy of astropy table in a browser window.
        Convert underscores to spaces in column headers to allow wrapping.
        """
        out = table.copy(copy_data=False)
        for key in out.keys():
            newkey = key.replace('_', ' ')
            if newkey != key:
                out.rename_column(key, newkey)
        out.show_in_browser(jsviewer=True, show_row_index=False)

def main():
    args = arguments()
    sql = Sqlfile(args.sqlfile)
    if args.tablename:
        table = sql.table(args.tablename, browser=True)
    else:
        print('specify a table name as the second argument:')
        for name in sql.tablenames:
            print(name)

if __name__ == "__main__":
    main()
