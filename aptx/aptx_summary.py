#!/usr/bin/env python

import argparse
import aptx

parser = argparse.ArgumentParser(
    description='Print summary of .aptx file to terminal.',
    epilog='example: aptx_summary.py 12345.aptx')
parser.add_argument('aptxfiles', nargs='+', help='filename of .aptx file')
args = parser.parse_args()

for aptxfile in args.aptxfiles:
    aptx.Proposal(aptxfile).summary()
    print('-----')
