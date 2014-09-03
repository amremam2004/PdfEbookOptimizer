'''

@author: aemam
'''

ENABLE_PICKLE = False
import subprocess
import json
import pickle
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from SelectedPage import SelectedPages
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from PageParser import PageParser
from PdfBuilder import PdfBuilder
import os

class PdfFileParser(object):
    def __init__(self, infile, 
                 outfile = None, password = None, selectedpages = None, 
                 maxSplit = 3, W= 1440.0, H=1080.0,
                 outputJson = False, trimbox=None, trimboxes=None, exclude=False, debug=0):
        self.args = {a[0]:a[1] for a in locals().items() if a[0] not in ['self','outputJson']}
        self.outputJson = outputJson
        self.DEBUG = debug
        self.picklefile = infile + '.pickle'
        self.selectedpages = selectedpages
        self.pickleLoaded = False
        self.savedconfig = None
        self.coords = []
        self.pagesCoords = []
        self.trimbox = trimbox
        self.trimboxes = trimboxes
        self.exclude = exclude
 
        self.pageRanges=SelectedPages(selectedpages)
        
        if ENABLE_PICKLE and os.path.isfile(self.picklefile) :
            try:
                with open(self.picklefile, 'rb') as f:
                    self.savedconfig = pickle.load(f)
                    savedargs = self.savedconfig['args']
                    equal = True
                    for k,v in self.args.items():
                        if k == 'selectedpages':
                            if v not in SelectedPages(savedargs[k]):
                                equal = False
                        elif k not in savedargs:
                            equal = False
                        elif v != savedargs[k]:
                            equal = False
                        if not equal:
                            break
                            
                        
                    if equal:
                        self.pickleLoaded = True
                        self.pagesCoords = self.savedconfig['pagesCoords']
            except Exception, e:
                print e

        self.fname = infile
        self.W = float(W)
        self.H = float(H)
        self.maxSplit = maxSplit
        self.outfile = outfile
        if self.outfile == None:
            outFilename, outExt = os.path.splitext(infile)
            self.outfile = outFilename + '-out' + outExt
            if not (self.selectedpages == None or self.selectedpages==''):
                outFilename, outExt = os.path.splitext(self.outfile)
                self.outfile = '%s(%s)%s' %(outFilename, self.selectedpages, outExt)
        if os.path.isfile(self.outfile) :
            i=1
            outfile, outExt = os.path.splitext(self.outfile) 
            while os.path.isfile("%s(%d)%s"%(outfile, i, outExt)):
                i+=1
            self.outfile= "%s%d%s"%(outfile, i, outExt) 
            
            
        
        self.password = password
        self.endPage = self.pageRanges.getEndPage(30000)-1  # 1 base vs 2 base

        self.inFile = open(self.fname, 'rb')
        self.parser = PDFParser(self.inFile)
        self.document = PDFDocument(self.parser)
        self.rsrcmgr = PDFResourceManager()
        self.laparams = LAParams()
        if not self.pickleLoaded:    
            self.device = PDFPageAggregator(self.rsrcmgr, laparams=self.laparams)
            self.interpreter = PDFPageInterpreter(self.rsrcmgr, self.device)
            self.pagesEnumerator =  enumerate(PDFPage.create_pages(self.document))

    def getpagebox(self, page):
        m=c=None
        if hasattr(page, "mediabox"):
            m=page.mediabox
        if hasattr(page, "cropbox"):
            c=page.cropbox
        pagebox = (min(m[0], c[0]),min(m[1],c[1]), max(m[2],c[2]), max(m[3],c[3])) if c!=None and m!=None else \
                m if m !=None else c
        if pagebox[0] > pagebox[2]:
            pagebox=(2*pagebox[2]-pagebox[0], pagebox[1], pagebox[2], pagebox[3])
        if pagebox[1] > pagebox[3]:
            pagebox=(pagebox[0], 2*pagebox[3]-pagebox[1], pagebox[2], pagebox[3])
        return pagebox
        
    def GetMaxScale(self, combinedLines):
        if combinedLines == None or len(combinedLines) == 0:
            return 1000
        from itertools import groupby
        Xs = [(x,list(v)) for x,v in groupby(combinedLines, key=lambda v: v[0])]
        Xs.sort(key=lambda x:len(x[1]),reverse=True)
        xs = Xs[0][1]
        if len(xs)<=1:
            return 1000
        Ws = [(x,list(v)) for x,v in groupby(xs, key=lambda v: v[2]-v[1])]
        Ws.sort(key=lambda x:len(x[1]), reverse=True)
        if len(Ws[0][1]) == 1:
            #use median
            Ws = [x[2]-x[0] for x in xs]
            Ws.sort()
            w = Ws[len(Ws)/2]
            avg = sum(Ws)/len(Ws)
            import math
            stddev = math.sqrt(sum([(x-avg)**2 for x in Ws])/len(Ws))
            Ws1 = [x for x in Ws if abs(x-avg) <=stddev]
            avg2 = sum(Ws1)/len(Ws1)
            w = Ws1[0]
                        
        else:
            w = Ws[0][0]
        maxScale= self.W/w
        return maxScale
    
    def process(self):
        print ""
        pdfbuilder = PdfBuilder(self.fname, self.coords, self.W, self.H, self.rsrcmgr, self.laparams)
        for (pageno, page) in self.pagesEnumerator:
            if pageno > self.endPage:
                break
            if not self.pageRanges.isInRange(pageno+1):
                continue
            self.interpreter.process_page(page)
            # receive the LTPage object for the page.
            layout = self.device.get_result()
            print "processing page %d                                         \n" %(pageno+1),
            trimboxes = [self.trimbox]
            if self.trimboxes != None and pageno in self.trimboxes:
                trimboxes = self.trimboxes[pageno]
             
            pageParser= PageParser(layout, self.maxSplit, self.W, self.H, trimboxes, self.exclude, pagebox=self.getpagebox(page))
            pageCoords = pageParser.process()
            maxScale = self.GetMaxScale(pageCoords['combinedLines'])
            pageCoords['pageno']= pageno
            crops = None
            if pageCoords != None:
                crops = pageCoords['crops']
            
            if crops == None or len(crops)==0:
                continue
            self.coords.append((pageno, crops))
            self.pagesCoords.append(pageCoords)
            pdfbuilder.processTrimmed(page, pageno, crops, maxScale = maxScale) #self.outputJson)

        self.scales = pdfbuilder.endProcess()
        if self.DEBUG > 0:
            with open(self.picklefile, 'wb') as f:
                procResult = {'args': self.args, 'pagesCoords':self.pagesCoords, 'scales':self.scales}
                pickle.dump(procResult, f)

        if self.coords == None or len(self.coords) ==0:
            print "No objects found\r"
            return
        
        with open(self.fname + '.json', 'wb') as f:
            f.write(json.dumps({'scales':self.scales}))
        try:
            params = [r"java.exe", "-cp", r"pdf2ereader.jar", "jpdftoepub.TrimPdf", "crop", self.fname, self.outfile,self.fname + '.json']
            print ' '.join(params)
            p = subprocess.Popen(params)
            p.wait()
            #sself.DEBUG = 1
            if p.returncode == 0 and not (self.DEBUG >0):
                os.remove(self.fname + '.json')
                os.remove(self.fname + ".cropped-streams")
            print "\nDone"
        except Exception, e:
            print e
            
                
    
    