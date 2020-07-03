#!/usr/bin/python3

# Brock Palen
# brockp@umich.edu
# 7/2020
#
#  prep a directory for placement in dataden
#  process:
#    1. run mpiFileUtils / dwalk  (deafault sort in name / path order) all files < minsize
#    2. Take resulting list build tar lists by summing size until > tarsize (before compression)
#    3. Tar each list:  OR --dryrun create list with est size
#       a. Create Index file of contents
#       b. Optionally compress -z / -j  with gzip/pigz bzip/lbzip2 if installed
#       c. Optionally purge 
#    4. (?) Kick out optimized untar script (pigz / lbzip2)

## TODO
# * filter and produce list to feed to scp/globus?
# * allow direct handoff to Globus CLI
# * mpibzip2

import shutil, pathlib, re
from tempfile import mkstemp

def find_gzip():
    """find pigz if installed in PATH otherwise return gzip"""
    pigz =  shutil.which(pbcopy)
    gzip =  shutil.which(gzip)
    if pigz:
       return pigz
    elif gzip:
       return gzip
    else:
       raise Exception("gzip compression but no gzip or pigz found in PATH")

def find_bzip():
    """find pigz if installed in PATH otherwise return gzip"""
    lbzip2 =  shutil.which(lbzip2)
    pbzip2 =  shutil.which(pbzip2)
    bzip2 =  shutil.which(bzip2)
    if lbzip2:
       return lbzip2
    elif pbzip2:
       return pbzip2
    elif bzip2:
       return bzip2
    else:
       raise Exception("gzip compression but no gzip or pigz found in PATH")

class DwalkLine:
    def __init__(self, line=False):
        """parse dwalk output line"""
        #-rw-r--r-- bennet support 578.000  B Oct 22 2019 09:35 /scratch/support_root/support/bennet/haoransh/DDA_2D_60x70_kulow_1.batch
        match = re.match(r"\S+\s+\S+\s+\S+\s+(\d+\.\d+)\s+(\S+)\s+.+\s(/.+)", line)
        #print(f"units: {match[1]}") #size
        #print(f"units: {match[2]}") #units
        #print(f"file: {match[3]}")  #path
        self.size = self._normilizeunits(units=match[2], count=float(match[1]))  #size in bytes
        self.path = match[3]

    def _normilizeunits(self, units=False, count=False):
        """convert size by SI units to Bytes"""
        if ( units == 'B' ):
           return count
        elif ( units == 'KB' ):
           return 1000*count 
        elif ( units == 'MB' ):
           return 1000*1000*count
        elif ( units == 'GB' ):
           return 1000*1000*1000*count
        elif ( units == 'TB' ):
           return 1000*1000*1000*1000*count
        elif ( units == 'PB' ):
           return 1000*1000*1000*1000*count
        else:
           raise Exception(f"{units} is not a known SI unit")


class DwalkParser:
    def __init__(self, path=False):
        # check that path exists
        path = pathlib.Path(path)
        self.indexcount = 1
        if path.is_file():
           self.path = path.open()
        else:
           raise Exception(f"{self.path} doesn't exist")

    def tarlist(self,
                prefix='archivetar',   # prefix for files
                minsize=1e9*100):      # min size sum of all files in list
                                       # OUT tar list suitable for gnutar
                                       # OUT index list
                """takes dwalk output walks though until sum(size) >= minsize"""

                tartmp_p = pathlib.Path.cwd() / f'{prefix}-{self.indexcount}.tartmp.txt' # list of files suitable for gnutar
                index_p  = pathlib.Path.cwd() / f"{prefix}-{self.indexcount}.index.txt"
                sizesum = 0  # size in bytes thus far
                index = index_p.open('w')
                tartmp = tartmp_p.open('w')
                for line in self.path:
                    pl = DwalkLine(line=line)
                    sizesum += pl.size
                    index.write(line)    #already has newline
                    tartmp.write(f"{pl.path}\n")  # write doesn't append newline
                    if sizesum >= minsize:
                       # max size in tar reached
                       self.indexcount+=1
                       tartmp.close()
                       index.close()
                       print(f"Minimum Archive Size {minsize} reached, Expected size: {sizesum}")
                       yield index_p, tartmp_p
                       # continue after yeilding file paths back to program
                       sizesum = 0
                       tartmp_p = pathlib.Path.cwd() / f'{prefix}-{self.indexcount}.tartmp.txt' # list of files suitable for gnutar
                       index_p  = pathlib.Path.cwd() / f"{prefix}-{self.indexcount}.index.txt"
                       index = index_p.open('w')
                       tartmp = tartmp_p.open('w')
                index.close()   # close and return for final round
                tartmp.close()
                yield index_p, tartmp_p


       
                 