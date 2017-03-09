#!/usr/bin/env python

# Import packages.
import argparse
import aptx
from astropy.time import Time

# Command line argument handler.
parser = argparse.ArgumentParser(
    description='Extract guide star windows from a .aptx file',
    epilog='example: aptx_gswin.py 98765 1')
parser.add_argument('root', help='name of .aptx file without the extension')
parser.add_argument('obs', type=int, help='observation number')
parser.add_argument('-tform', choices=['unix','isot','decimalyear'],
        default='unix', help='output time format')
args = parser.parse_args()

# Get XML element for requested observation.
aptxfile = args.root + '.aptx'
obsstr = '{}'.format(args.obs)
prop = aptx.Proposal(aptxfile)
obs = prop.observation(obsstr)

# Get XML element with results from visit planner for specified observation.
toolvalues = obs.elem.findall('.//apt:ToolValue',prop.ns)
if not toolvalues:
    raise Exception('Observation {} has no visit planner data'.format(obsstr))

# Loop through visits in visit planner results.
type = 'guide-star'
windows = []
for e in toolvalues:

# Parse observation and visit header.
    key = e.get('Name')
    tag,progid,obsid,visid = key.split(':')
    obsid = int(obsid)
    visid = int(visid)
#   print('Obs={}, Visit={}'.format(obsid,visid))

# Check that visit scheduling window is up to date.
    vp = aptx.etree.fromstring(e.text)
    vsw = vp.xpath('.//StVisitSchedulingWindows')
    if vsw[0].get('UpToDate') == 'false':
        raise Exception('Observation {} is not up to date.'
                ' Run visit planner.'.format(obsstr))

# Get XML element for guide star scheduling windows.
    xp = (".//StVisitSchedulingWindows"
            "/StConstraintSchedulingWindows"
            "[@Type='" + type + "']")
    gs = vp.xpath(xp)[0]
    pcf = gs.get('StSchedulingPCF').split()
#   print(pcf)

# Loop through words in scheduling data, parsing V3PA, probability, and time.
    t2 = None
    prev = None
    for str in pcf:

# Process the valid range of V3PA position angle.
        if ':' in str:
            a1 = float(str.split(':')[0])
            a2 = float(str.split(':')[1])

# Process a "probability". 1 is good availability. 0 is bad.
        elif '.' in str:
            p = float(str)

# Process a time. Input format is unix milliseconds. Output as specified.
        else:
            if args.tform == 'unix':
                t = int(int(str)/1000)
            elif args.tform == 'isot':
                t = Time(int(str)/1000, format='unix').isot[:-4]
            elif args.tform == 'decimalyear':
                t = Time(int(str)/1000, format='unix').decimalyear
            if t2 is None:
                t2 = t
            else:
                t1 = t2
                t2 = t
                if p > 0:

# Merge current window with previous if time interval is being extended.
                    curr = (obsid,visid,t1,t2,a1,a2,p)
                    if prev is not None:
                        if obsid == prev[0] and visid == prev[1] \
                                and t1 == prev[3] \
                                and a1 == prev[4] and a2 == prev[5] \
                                and p == prev[6]:
                            curr = windows.pop()
                            curr = (prev[0],prev[1],prev[2],t2,
                                    prev[4],prev[5],prev[6])
                    windows.append(curr)
                    prev = curr
            p = 0.0
            a1 = 0.0
            a2 = 0.0

# Write results to output file. Output format depends on time format.
if args.tform == 'decimalyear':
   tout = '{:.5f}'
else:
   tout = '{}'
out = '{:3d} {:3d} ' + tout + ' ' + tout + ' {:7.3f} {:7.3f} {:.6f}\n'
gswinfile = args.root + '_{:d}'.format(obsid) + '.gswin'
print('writing results to {}'.format(gswinfile))
with open(gswinfile, 'w') as file:
    for window in windows:
        file.write(out.format(*window))
