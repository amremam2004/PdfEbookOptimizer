'''

@author: aemam
'''

from pdfminer.pdfparser import PDFParser, STRICT
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFPageInterpreter, PDFContentParser, PDFResourceManager, PDFInterpreterError
from pdfminer.pdfdevice import  PDFTextDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from pdfminer.psparser import  PSEOF, PSKeyword, keyword_name
from pdfminer.pdftypes import  stream_value
from SelectedPage import SelectedPages
from PageParser import PageParser
import os
#from pdfminer import PSBaseParser
from io import BytesIO
import sys
import traceback
import json
import subprocess

class MyPDFContentParser(PDFContentParser):

    def __init__(self, streams):
        PDFContentParser.__init__(self, streams)

    def fillbuf(self):
        if self.charpos < len(self.buf):
            return
        while 1:
            self.fillfp()
            self.buf = self.fp.read(self.BUFSIZ)
            if self.buf:
                break
            self.fp = None
        self.charpos = 0
        return





class MyPDFPageInterpreter(PDFPageInterpreter):

    def __init__(self, rsrcmgr, device):
        super(MyPDFPageInterpreter, self).__init__(rsrcmgr, device)
        return

    def dup(self):
        return PDFPageInterpreter(self.rsrcmgr, self.device)

    def process_page(self, page, nboxes, exclude=False):
        self.exclude = exclude
        self.nboxes=nboxes
        self.filteredstreams = [BytesIO() for _ in range(self.nboxes if not self.exclude else 1)]
            
        PDFPageInterpreter.process_page(self, page)
        
    def execute(self, streams):
        for i,stream in enumerate(streams):
            if i != 0:
                for j in range(self.nboxes if not self.exclude else 1):
                    self.filteredstreams[j].write(b'\n')
            
            self.curpath = []
            self.execute1(stream)
            
            
    def execute1(self, stream):
        
        strmdata = stream_value(stream).get_data()
        prevpos = 0
        fulltokenlist = []
        try:
            PDFContentParser.BUFSIZ = 20*1024*1024
            parser = MyPDFContentParser([stream])
            parser.BUFSIZ = 20*1024*1024
        except PSEOF:
            return
        while 1:
            try:
                (pos, obj) = parser.nextobject()
            except PSEOF:
                break
            if isinstance(obj, PSKeyword):
                inpath = False
                firstpath = False
                ispath = False
                name = keyword_name(obj)
                if len(self.curpath) > 0:
                    inpath = True
                if name in ['m','l','c','v','y','h','re', 'S','f','F','f*','F*','B','B*','b','b*','n']:
                    ispath = True
                    if not inpath: 
                        firstpath=True
                    inpath = True

                curpos = pos + len(name)
                if ispath:
                    if firstpath:
                        fulltokenlist.append({'name':name, 'startpos':prevpos, 'endpos':curpos, 'view':[True]*self.nboxes})
                    else:
                        fulltokenlist[-1]['endpos'] = curpos
                        
                else:        
                    fulltokenlist.append({'name':name, 'startpos':prevpos, 'endpos':curpos, 'view':[True]*self.nboxes})
 
                prevpos = curpos
                        
                        

                method = 'do_%s' % name.replace('*', '_a').replace('"', '_w').replace("'", '_q')
                if hasattr(self, method):
                    func = getattr(self, method)
                    nargs = func.func_code.co_argcount-1
                    if nargs:
                        args = self.pop(nargs)
                        if 2 <= self.debug:
                            print >>sys.stderr, 'exec: %s %r' % (name, args)

                            
                        if len(args) == nargs:
                            res = func(*args)
                            if not(res == None or False not in res):
                                fulltokenlist[-1]['view'] = res
                            
                                    
                                
                    else:
                        if 2 <= self.debug:
                            print >>sys.stderr, 'exec: %s %s' % (method, name)
                        res = func()
                        if not(res == None or False not in res):
                            fulltokenlist[-1]['view']=res
                            
                else:
                    pass
                    if STRICT:
                        raise PDFInterpreterError('Unknown operator: %r' % name)
            else:
                self.push(obj)
                
        for j in range(self.nboxes if not self.exclude else 1):
            tokenlist = [a for a in fulltokenlist if a['view'][j]==True]
            tokenlist = [a for i,a in enumerate(tokenlist) if not (a['name']=='Tf' and i<len(tokenlist)-2 and tokenlist[i+1]['name']=='Td' and tokenlist[i+2]['name']=='Tf')]
            for a in tokenlist:
                self.filteredstreams[j].write(strmdata[a['startpos']:a['endpos']])
        return    

    def do_S(self):
        PDFPageInterpreter.do_S(self)
        return self.device.showpath
    def do_f(self):
        PDFPageInterpreter.do_f(self)
        return self.device.showpath
    
    do_F = do_f
    def do_f_a(self): 
        PDFPageInterpreter.do_f_a(self)
        return self.device.showpath

    def do_B(self):
        PDFPageInterpreter.do_B(self)
        return self.device.showpath

    def do_B_a(self):
        PDFPageInterpreter.do_B_a(self)
        return self.device.showpath

    def do_TJ(self, seq):
        PDFPageInterpreter.do_TJ(self, seq)
        return self.device.showtext
    def do_Tj(self, s):
        return self.do_TJ([s])
    def do_EI(self, obj):
        PDFPageInterpreter.do_EI(self, obj)
        return self.device.showfigure
    def do_Do(self, xobjid):
        PDFPageInterpreter.do_Do(self, xobjid)
        return self.device.showfigure
    
    
class MyPDFPageAggregator(PDFPageAggregator):

    def __init__(self, rsrcmgr,boxes=[(0,0,1080.0, 1440.0)], pageno=1, laparams=None, onlyInside=False):
        self.setCropBoxes(boxes)
        self.onlyInside = onlyInside
        self.inFigure = False
        PDFPageAggregator.__init__(self, rsrcmgr, pageno=pageno, laparams=laparams)

    def setCropBoxes(self, boxes, exclude = False):
        self.boxes = boxes
        self.exclude = exclude
        self.nboxes = len(self.boxes)
        self.showtext = [True]*(self.nboxes if not self.exclude else 1)
        self.showfigure = [True]*(self.nboxes if not self.exclude else 1)
        self.showpath = [True]*(self.nboxes if not self.exclude else 1)
            

    def intersect(self, itembox=None):
        if itembox == None:
            itembox = self.cur_item.bbox
        boxes = self.boxes
        result = []
        if not self.exclude:
            if self.onlyInside:
                for box in boxes:
                    result.append((itembox[0] >= box[0] and itembox[2]<=box[2] and itembox[1] >=box[1] and itembox[3] <=box[3])
                                  or
                                  (box[0] >= itembox[0] and box[2]<=itembox[2] and box[1] >=itembox[1] and box[3] <=itembox[3]))
            else:
                for box in boxes:
                    result.append(not(box[0] >= itembox[2] or itembox[0] >= box[2] or box[1] >= itembox[3] or itembox[1] >= box[3]))
                
        else:
            result.append(True)
            if self.onlyInside:
                for box in boxes:
                    result[0] = result[0] and not (itembox[0] >= box[0] and 
                                                   itembox[2] <=box[2] and 
                                                   itembox[1] >= box[1] and 
                                                   itembox[3] <= box[3])
                    if not result[0]:
                        break
            else:
                for box in boxes:
                    result[0] = result[0] and not (((itembox[0] >= box[0] and itembox[0] <= box[2]) or 
                                                    (itembox[2] >= box[0] and itembox[2] <= box[2])) and
                                                   ((itembox[1] >= box[1] and itembox[1]<= box[3]) or 
                                                    (itembox[3] >= box[1] and itembox[3] <= box[3])))
                    if not result[0]:
                        break
                
                    
        return result
    
    def begin_page(self, page, ctm):
        PDFPageAggregator.begin_page(self, page, ctm)
        
    def end_page(self, page):
        return

    
    def begin_figure(self, name, bbox, matrix):
        self.inFigure = True
        PDFPageAggregator.begin_figure(self, name, bbox, matrix)
        self.showfigure = [False]*(self.nboxes if not self.exclude else 1)

    def end_figure(self, A):
        curBox = list(self.cur_item.bbox)
        PDFPageAggregator.end_figure(self, A)
        showfigure = self.intersect(curBox)
        self.showfigure = [x[0] or x[1] for x in zip(self.showfigure, showfigure)]
        self.inFigure = False

    def render_image(self, name, stream):
        PDFPageAggregator.render_image(self, name, stream)

    def paint_path(self, gstate, stroke, fill, evenodd, path):
        curItem = self.cur_item 
        l1 = len(curItem)
        PDFPageAggregator.paint_path(self, gstate, stroke, fill, evenodd, path)
        l2 = len(curItem)
        
        b = reduce(lambda x,y: PageParser.mergeBoxes(x, y.bbox), curItem._objs[l1:l2], None )
        if self.inFigure:
            self.showfigure = [x[0] or x[1] for x in zip(self.showfigure, self.intersect(b))]
        else:
            self.showpath = self.intersect(b)

    def render_char(self, matrix, font, fontsize, scaling, rise, cid):
        adv = PDFPageAggregator.render_char(self, matrix, font, fontsize, scaling, rise, cid)
        return adv

    def render_string(self, textstate, seq):
        curItem = self.cur_item 
        l1 = len(curItem)
        PDFTextDevice.render_string(self, textstate, seq)
        l2 = len(curItem)
        
        b = reduce(lambda x,y: PageParser.mergeBoxes(x, y.bbox), curItem._objs[l1:l2], None )
        if self.inFigure:
            self.showfigure = [x[0] or x[1] for x in zip(self.showfigure, self.intersect(b))]
        else:
            self.showtext = self.intersect(b)


def TrimPdfFile(infile, outfile, box=None, boxes = None, selectedpages=None, exclude=False, debug=0):
    fp = open(infile, 'rb')
    fo = file(infile + ".streams", "wb")
    pageRanges=SelectedPages(selectedpages)
    DEBUG = debug
    parser = PDFParser(fp)
    document = PDFDocument(parser) #, password)
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = MyPDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = MyPDFPageInterpreter(rsrcmgr, device)
    _debug = interpreter.debug
    
    _stderr = sys.stderr
    sys.stderr = sys.stdout
    streamlist = []
    for (pageno,page) in enumerate(PDFPage.create_pages(document)):
        if not pageRanges.isInRange(pageno+1):
            continue

        print "trimming page %d" % (pageno+1)
        mboxes = [box]
        if boxes != None and pageno in boxes:
            mboxes = boxes[pageno]
            
        #print box    

        #print "bounding box " + str(mbox)
        device.setCropBoxes(mboxes, exclude)

        interpreter.process_page(page, len(mboxes), exclude)
        fo.write("\n#################    %d     #####################\n"%(pageno+1))
        startpos = fo.tell()
        fo.write(interpreter.filteredstreams[0].getvalue())
        endpos = fo.tell()
        streamlist.append((pageno, startpos, endpos-startpos))
            

    with open(infile + '.trim.json', 'wb') as f:
        f.write(json.dumps({'streams':streamlist}))
    
    p = subprocess.Popen([r"java.exe", "-cp", r"pdf2ereader.jar", "jpdftoepub.TrimPdf","trim", infile, outfile])
    p.wait()
    sys.stderr = _stderr  
    fp.close()
    fo.close()
    #sdebug = 1
    if debug == 0:
        os.remove(infile + ".trim.json") 
        os.remove(infile + ".streams")       

    
import ast
if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = infile + ".trimmed-streams"
    box = None
    if len(sys.argv) >2:
        box = ast.literal_eval(sys.argv[2])
    if len(sys.argv) > 3:
        outfile = sys.argv[3]
        
    try:
        TrimPdfFile(infile, outfile, boxes=[box])
    except Exception, e:
        print e
        tb = traceback.format_exc()
        print tb

    sys.exit(0)
