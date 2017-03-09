import os
import subprocess
import zipfile
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from lxml import etree

# Define class to handle target specification in an aptx file
class Target:
    """Represent an APT target.

    Parameters
    ----------
    elem : lxml etree `_Element` object containing an XML <Target> element
    """

    def __init__(self, elem):
        self.elem = elem
        self.ns = elem.nsmap
        self.ns['apt'] = self.ns.pop(None)
        self.number = elem.find('.//apt:Number', self.ns)
        self.propname = elem.find('.//apt:TargetName', self.ns)
        self.archname = elem.find('.//apt:TargetID', self.ns)
        self.coord = elem.find('.//apt:EquatorialCoordinates', self.ns)
        self.pmra = elem.find('.//apt:RAProperMotion', self.ns)
        self.pmrau = elem.find('.//apt:RAProperMotionUnits', self.ns)
        self.pmdec = elem.find('.//apt:DecProperMotion', self.ns)
        self.pmdecu = elem.find('.//apt:DecProperMotionUnits', self.ns)

    def xmldump(self):
        """Print to screen contents of XML <Target> element.
        """
        for line in etree.tostring(self.elem).splitlines():
            if '<Target ' not in line and '</Target>' not in line:
                print(line)

    def summary(self):
        _eqstr = self.coord.attrib['Value']
        _rastr = ' '.join(_eqstr.split(' ')[0:3])
        _destr = ' '.join(_eqstr.split(' ')[3:6])
        _eqcoo = SkyCoord(_eqstr, unit=(u.hourangle,u.deg))
        print("{}='{}', {}='{}', {}='{}'".format(
                'Number',self.number.text,
                'Proposal Name',self.propname.text,
                'Archive Name',self.archname.text))
        print("{}='{}' ({} deg), {}='{}' ({} deg)".format(
                'RA',_rastr,_eqcoo.ra.degree,
                'Dec',_destr,_eqcoo.dec.degree))
        print("{}={} {}, {}={} {}".format(
                'pmRA',self.pmra.text,self.pmrau.text or '',
                'pmDec',self.pmdec.text,self.pmdecu.text or ''))

    def update(self,number=None,propname=None,archname=None,
            coord=None,pmra=None,pmdec=None,pmrau=None,pmdecu=None):
        if number is not None:
            self.number.text=number
        if propname is not None:
            self.propname.text=propname
        if archname is not None:
            self.archname.text=archname
        if coord is not None:
            self.coord.attrib['Value']=coord.to_string(style='hmsdms',sep=' ')
        if pmra is not None:
            self.pmra.text=pmra
        if pmdec is not None:
            self.pmdec.text=pmdec
        if pmrau is not None:
            self.pmrau.text=pmrau
        if pmdecu is not None:
            self.pmdecu.text=pmdecu

class Template:
    def __init__(self, elem):
        self.elem = elem
        self.ns = elem.nsmap
        self.ns['apt'] = self.ns.pop(None)
        _elem1 = self.elem.getchildren()[0]
        self.templateid = _elem1.prefix
        try:
            self.templatename = _elem1.tag.split('}')[1]
        except:
            self.templatename = None

    def summary(self):
        print("{}='{}', {}='{}'".format(
                '  Template ID',self.templateid,
                'Name',self.templatename))

    def xmldump(self):
        for line in etree.tostring(self.elem).splitlines():
            lstr = line.decode()
            if '<Template ' not in lstr and '</Template>' not in lstr:
                print(line)

class MosaicParameters:
    def __init__(self, elem):
        self.elem = elem
        self.ns = elem.nsmap
        self.ns['apt'] = self.ns.pop(None)
        self.rows = elem.find('.//apt:Rows', self.ns)
        self.columns = elem.find('.//apt:Columns', self.ns)
        self.rowoverlap = elem.find('.//apt:RowOverlapPercent', self.ns)
        self.coloverlap = elem.find('.//apt:ColumnOverlapPercent', self.ns)
        self.xskew = elem.find('.//apt:SkewDegreesX', self.ns)
        self.yskew = elem.find('.//apt:SkewDegreesY', self.ns)

    def summary(self):
        print("{}={}, {}={}%, {}={} degrees".format(
                '  Mosaic Rows', self.rows.text,
                'Overlap', self.rowoverlap.text,
                'Xskew', self.xskew.text))
        print("{}={}, {}={}%, {}={} degrees".format(
                '         Cols', self.columns.text,
                'Overlap', self.coloverlap.text,
                'Yskew', self.yskew.text))

    def xmldump(self):
        key = 'MosaicParameters'
        for line in etree.tostring(self.elem).splitlines():
            lstr = line.decode()
            if '<'+key+'>' not in lstr and '</'+key+'>' not in lstr:
                print(line)

class Observation:
    def __init__(self, elem):
        self.elem = elem
        self.ns = elem.nsmap
        self.ns['apt'] = self.ns.pop(None)
        self.number = elem.find('.//apt:Number', self.ns)
        self.targetid = elem.find('.//apt:TargetID', self.ns)
        self.instrument = elem.find('.//apt:Instrument', self.ns)

    def xmldump(self):
        for line in etree.tostring(self.elem).splitlines():
            lstr = line.decode()
            if '<Observation ' not in lstr and '</Observation>' not in lstr:
                print(line)

    def template(self, name=None):
        _xpath = './/apt:Template'
        _elem = self.elem.xpath(_xpath, namespaces=self.ns)[0]
        return Template(_elem)

    def mosaic(self):
        _xpath = './/apt:MosaicParameters'
        _elem = self.elem.xpath(_xpath, namespaces=self.ns)[0]
        return MosaicParameters(_elem)

    def summary(self):
        print("{}='{}', {}='{}'".format(
                'Observation Number',self.number.text,
                'Instrument',self.instrument.text))
        print("{}='{}'".format(
                '  TargetID',self.targetid.text))
        temp = self.template()
        temp.summary()

    def update(self,number=None,targetid=None,instrument=None,
            mosaic=None):
        if number is not None:
            self.number.text=number
        if targetid is not None:
            self.targetid.text=targetid
        if instrument is not None:
            self.instrument.text=instrument
        if mosaic is not None:
            _xpath = './/apt:MosaicParameters'
            _old = self.elem.xpath(_xpath, namespaces=self.ns)[0]
            _old.getparent().replace(_old, mosaic.elem)

class Proposal:
    def __init__(self, aptxfile):
        with zipfile.ZipFile(aptxfile) as zfile:
            self.zdata = {name: zfile.read(name) for name in zfile.namelist()}
        self.aptxfile = aptxfile
        self.xmlfile = os.path.splitext(aptxfile)[0]+'.xml'
        self.doctype = self.zdata[self.xmlfile].splitlines()[0]
        self.root = etree.fromstring(self.zdata[self.xmlfile])
        self.ns = self.root.nsmap
        self.ns['apt'] = self.ns.pop(None)
        self.schemaversion = self.root.get('schemaVersion')

    def xmldump(self):
        for line in etree.tostring(self.root).splitlines():
            print(line)

    def target(self, targnum, name=None):
        _xpath = './/apt:Target/apt:Number[text()="' + targnum + '"]'
        _elem = self.root.xpath(_xpath, namespaces=self.ns)[0]
        if _elem is not None:
            return Target(_elem.getparent())
        else:
            return None

    def targnums(self):
        _xpath = './/apt:Target/apt:Number'
        targnums = sorted({e.text for e in self.root.findall(_xpath, self.ns)})
        return targnums

    def observation(self, obsnum, name=None):
        _xpath = './/apt:Observation/apt:Number[text()="' + obsnum + '"]'
        _elem = self.root.xpath(_xpath, namespaces=self.ns)
        if not _elem:
            raise ValueError('Proposal has no observation {}'
                    .format(obsnum))
        else:
            return Observation(_elem[0].getparent())

    def obsnums(self):
        _xpath = './/apt:Observation/apt:Number'
        obsnums = sorted({e.text for e in self.root.findall(_xpath, self.ns)})
        return obsnums

    def summary(self):
        print("{}='{}', {}='{}'".format(
                'File',self.aptxfile,
                'schemaVersion',self.schemaversion))
        for obsnum in self.obsnums():
            self.observation(obsnum).summary()

    def update(self, target=None, observation=None):
        if target is not None:
            _xpath = './/apt:Target/apt:Number[text()="' \
                    + target.number.text + '"]'
            _number = self.root.xpath(_xpath, namespaces=self.ns)[0]
            if _number is None:
                print('Target does not exist')
            else:
                _oldtarg = _number.getparent()
                _oldtarg.getparent().replace(_oldtarg, target.elem)
        if observation is not None:
            _xpath = './/apt:Observation/apt:Number[text()="' \
                    + observation.number.text + '"]'
            _number = self.root.xpath(_xpath, namespaces=self.ns)[0]
            if _number is None:
                print('Observation does not exist')
            else:
                _oldobs = _number.getparent()
                _oldobs.getparent().replace(_oldobs, observation.elem)

    def write(self, newfile):
        self.zdata[self.xmlfile] = etree.tostring(self.root,
                doctype=self.doctype)
        with zipfile.ZipFile(newfile, 'w') as zfile:
            for name in self.zdata.keys():
                zfile.writestr(name, self.zdata[name])
            zfile.close()

def run(aptxfile):
    aptdir = os.getenv('APTDIR')
    if aptdir is None:
        stddir = '/Applications'
        dirs = os.listdir(stddir)
        adirs = filter(lambda dir: dir.startswith('APT'), dirs)
        if adirs:
            aptdir = os.path.join(stddir,adirs[-1])
    apt = os.path.join(aptdir,'bin','apt')
    cmd = [apt,'-mode','STScI','-nogui','-nobackups', '-runall',
            '-export','pointing,times,smart_accounting',aptxfile]
    try:
        output = subprocess.check_output(cmd)
        print(output)
        returncode = 0
    except subprocess.CalledProcessError as e:
        output = e.output
        returncode = e.returncode
        print(output)

def pointing(pfile):
    _pnames = ('obsnum','visnum','targ','tile','expnum','dith',
            'aperture','targnum','propname','radeg','decdeg','xbase',
            'ybase','xdith','ydith','v2','v3','xidl',
            'yidl','level','type','expar','dkpar','ddist')
    _pdtype = ('i4','i4','i4','i4','i4','i4',
            'S99','i4','S99','f8','f8','f4',
            'f4','f4','f4','f4','f4','f4',
            'f4','S99','S99','i4','i4','f4')
    point = Table(names=_pnames, dtype=_pdtype)
    with open(pfile, 'r') as file:
        for line in file:
            words = line.split()
            if line.startswith('** Visit '):
                obsnum,visnum = line[9:].strip().split(':')
            elif len(words)==21 and words[0].isdigit():
                point.add_row([obsnum,visnum]+line.split()+[None])
            elif len(words)==22 and words[0].isdigit():
                point.add_row([obsnum,visnum]+line.split())
    return point

def times(tfile):
    _onames = ('obsnum','scidur','tcharge')
    _odtype = ('i4','i4', 'i4')
    obs = Table(names=_onames, dtype=_odtype)
    _vnames = ('obsnum','visnum','pdist','scidur','instoh','sam',
            'tslew','obsoh','schedoh','tcharge')
    _vdtype = ('i4','i4', 'f4','i4','i4','i4',
            'i4','i4','i4','i4')
    visit = Table(names=_vnames, dtype=_vdtype)
    _enames = ('obsnum','expnum','subarr','readout','tframe','ngroup',
            'nframe','grpgap','nint','tphotc','ndith','pdith',
            'sdith','nexp','tphot','expdur','exping')
    _edtype = ('i4','i4','S99','S99','f4','i4',
            'i4','i4','i4','f4','i4','i4',
            'i4','i4','f4','i4','i4')
    expo = Table(names=_enames, dtype=_edtype)
    with open(tfile, 'r') as file:
        for line in file:
            words = line.split()
            if line.startswith('* Observation '):
                obsnum = line.split()[-1]
            elif len(words)==2 and words[0].isdigit():
                obs.add_row([obsnum]+line.split())
            elif len(words)==16 and words[0].isdigit():
                expo.add_row([obsnum]+line.split())
            elif len(words)>9 and words[0].isdigit():
                line2 = line.replace('(','').replace(')','')
                visit.add_row([obsnum]+line2.split())
    return obs,visit,expo
