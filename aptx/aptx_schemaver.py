#!/usr/bin/env python

import aptx
import argparse
import textwrap
import os.path

parser = argparse.ArgumentParser(
    description='Print schema version of .aptx files.',
    epilog='example: aptx_schemaver.py *.aptx')
parser.add_argument('aptxfiles', nargs='+', help='aptx file specification')
args = parser.parse_args()

dict = {}
for aptxfile in args.aptxfiles:
    basename = os.path.basename(aptxfile)
    rootname = basename.rstrip('.aptx')
    try:
        version = aptx.Proposal(aptxfile).schemaversion
        dict[rootname] = version
    except:
        print('error reading schema version for {}'.format(aptx))

if len(dict) > 0:
    versions = sorted(set(dict.values()))
    for version in versions:
        rootnames = [k for k,v in dict.items() if v == version]
        out = 'schemaVersion=' + version + ': ' + ' '.join(rootnames)
        for line in textwrap.wrap(out, width=78):
            print(line)
