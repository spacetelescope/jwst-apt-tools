#!/usr/bin/env python

# Import packages.
import argparse
from astropy.table import Table

# Command line argument handler.
parser = argparse.ArgumentParser(
    description='Show in browser PPSDB table data (.sql) exported by APT.'
            "\nList available tables, if 'table' is not specified.",
    epilog='example: aptx_sql.py 98765.sql exposures')
parser.add_argument('sqlfile',help='SQL file exported by APT')
parser.add_argument('table',nargs='?',default='',help='PPSDB table name')
args = parser.parse_args()

# If table was not specified, print list of tables available in input file.
prefix='insert into '
if args.table == '':
    tlist=list()
    with open(args.sqlfile, 'r') as f:
        for line in f:
            if line[:len(prefix)] == prefix:
                tlist.append(line[len(prefix):line.find('(')].strip())
    print('\n'.join(sorted(set(tlist))))
    exit()

# Read and parse lines that begin with 'insert into <table> '.
# Store data for each row in a dictionary.
# Contruct a list of unique keywords for the requested table.
prefix='insert into '+args.table+' '
rows=list()
kset=set()
with open(args.sqlfile, 'r') as f:
    for line in f:
        if line[:len(prefix)] == prefix:
            kvstr=line[len(prefix):].replace(" ","").rstrip()
            keystr,valstr=kvstr.split('values')
            keys=keystr[1:-1].split(',')
            vals=valstr[1:-1].split(',')
            rows.append(dict(zip(keys,vals)))
            kset=kset.union(keys)
if not rows:
    print("'"+args.table+"' table data not found in "+args.sqlfile)
    exit()
ukeys=sorted(list(kset))

# Load data into astropy table one column at a time.
# Use empty string for missing entries.
# Display table in browser.
out=Table()
for ukey in ukeys:
    col=list()
    for row in rows:
        col.append(row.get(ukey,''))
    out[ukey.replace("_"," ")]=col
out.show_in_browser(jsviewer=True,show_row_index=False)
