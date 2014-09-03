'''

@author: aemam
'''

#!/usr/bin/env python
# encoding: utf-8

import sys
import os
from argparse import ArgumentParser
from PdfFileParser import PdfFileParser
from PdfPageCropper import TrimPdfFile
import traceback
__all__ = []
__version__ = 0.1
__date__ = '2013-12-20'
__updated__ = '2013-12-20'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

def main(argv=None):
    '''Command line options.'''
    program_name = os.path.basename(sys.argv[0])
    program_version = "v0.1"
    program_build_date = "%s" % __updated__

    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
    program_longdesc = '''A tool to transform PDF to be read in eReaders and Tablets'''
    program_license = "Copyright 2014                                           \
                Licensed under GPL"

    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = ArgumentParser(version=program_version_string, epilog=program_longdesc, description=program_license)
        parser.add_argument("-S", "--maxsplit", action="store", default=0, dest="maxsplit", type=int, required=False)
        parser.add_argument("-n", "--pages", dest="selectedpages", default="", required=False, help="specify pages 1,2-3")
        parser.add_argument("-j", "--json", dest="json", action="store_true", help="out json")
        parser.add_argument("-o", "--out", dest="outfile", required=False, help="output file", metavar="FILE")
        parser.add_argument("-W", "--width", dest="width", default=1440.0 , required=False, type=float, help="set width")
        parser.add_argument("-H", "--height", dest="height", default=1080.0, required=False, type=float, help="set height")
        parser.add_argument("-b", "--box", dest="box", nargs=4, type=float, action="store", required=False, help="trim box")
        parser.add_argument("-x", "--exclude", dest="exclude", default=False, action="store_true", required=False, help="Exclude Box")
        parser.add_argument("-D", "--debug", dest="debug", default=0, action="store", required=False, help="set debug")
        parser.add_argument("-p", "--password", dest="password", action="store",  required=False, help="password")
        
        parser.add_argument("-B", "--boxesfile", dest="boxesfile", action="store",  required=False, help="boxesfile",metavar="FILE")
        parser.add_argument("infile", help="set input pdf", metavar="FILE")
        opts = parser.parse_args(argv)
        DEBUG = opts.debug
        if opts.infile:
            print("infile = %s" % opts.infile)
        cropoutfile = opts.outfile
        cropinfile = opts.infile
        if DEBUG > 0:
            with open(opts.infile + ".cmdoptions", "wb") as f:
                print >> f, ' '.join([x.replace('"','') if ' ' not in x else '"' + x.replace('"','') + '"' for x in sys.argv])
        opts.boxes = None
        if opts.boxesfile != None:
            try:
                with open(opts.boxesfile) as f:
                    opts.boxes = eval(f.read())
            except Exception, e:
                print e
                
        if opts.box == None and opts.boxes == None and opts.maxsplit == 0:
                opts.maxsplit = 2
                
                
        if opts.maxsplit == 0:        
            triminfile = opts.infile
            trimoutfile = opts.outfile
            if opts.box != None or opts.boxes !=None:
                if trimoutfile == None:
                    trimoutfile = GetTempFileName(triminfile, "trimmed")
                TrimPdfFile(triminfile, trimoutfile, 
                            box=opts.box, 
                            boxes = opts.boxes, 
                            selectedpages=opts.selectedpages, 
                            exclude=opts.exclude,
                            debug=opts.debug)
        else: 
            if cropoutfile == None:
                cropoutfile = GetTempFileName(opts.infile, "cropped")   
            o = PdfFileParser(infile = cropinfile, 
                             outfile = cropoutfile,
                             selectedpages = opts.selectedpages,
                             password = opts.password, 
                             maxSplit = opts.maxsplit,
                             W = opts.width,
                             H = opts.height,
                             outputJson = opts.json,
                             trimbox=opts.box,
                             trimboxes = opts.boxes,
                             exclude=opts.exclude,
                             debug = opts.debug)
            o.process()
        if not (DEBUG > 0) and opts.boxesfile != None:
            os.remove(opts.boxesfile)
    except Exception as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        tb = traceback.format_exc()
        print tb
        return 2

def GetTempFileName(infile, part):
    outname, outext = os.path.splitext(infile)
    outfile = "%s-%s%s" %(outname, part, outext)
    if os.path.isfile(outfile) :
        i=1
        while True:
            outfile = "%s-%s(%d)%s"%(outname, part, i, outext)
            if not os.path.isfile(outfile):
                break
            i+=1
    return outfile


if __name__ == "__main__":
    ' '.join(sys.argv[1:])
    result = main(sys.argv[1:])
    sys.exit(result)
    