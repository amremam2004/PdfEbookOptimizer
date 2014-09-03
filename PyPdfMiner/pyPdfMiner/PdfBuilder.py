'''

@author: aemam
'''
from PdfPageCropper import MyPDFPageAggregator, MyPDFPageInterpreter
from PageParser import PageParser
import operator
class PdfBuilder(object):
    def __init__(self, fname, pagesCrops, W, H, rsrcmgr, laparams):
        self.fname = fname
        self.inFile = open(self.fname, "rb")
        self.pagesCrops = pagesCrops
        self.W = W
        self.H = H
        self.device = MyPDFPageAggregator(rsrcmgr, laparams=laparams, onlyInside=True)
        self.interpreter = MyPDFPageInterpreter(rsrcmgr, self.device)
        self.fo = file(self.fname + ".cropped-streams", "wb")
        self.scales = []
        self.outpageno = 0
        
    def reduceCrops(self, crops):
        scales = []
        if False:
            zeroHeight = [idx for idx in range(len(crops)) if crops[idx][3]-crops[idx][1]==0]
            reduced = False
            for idx in zeroHeight:
                prev = idx
                next = idx
                while True:
                    prev-=1
                    if prev < 0:
                        prev = None
                        break
                    if crops[prev]!= None:
                        break
                while True:
                    next+=1
                    if not (next < len(crops)):
                        next = None
                        break
                    if crops[next]!=None:
                        break
                if prev == None and next == None:
                    continue
                reduced = True
                if prev != None and next != None:
                    pass
                    #crops[p]
                elif prev != None:
                    crops[prev] = PageParser.mergeBoxes(crops[idx], crops[prev])
                    crops[idx] = None
                else:
                    crops[next] = PageParser.mergeBoxes(crops[idx], crops[next])
                    crops[idx] = None
    
            if reduced:
                try:
                    while True:
                        crops.remove(None)
                except ValueError:
                    pass
                
        for idx in range(len(crops)):
            _, _, _,  (scale, _, _) = self.getTransformation(crops[idx], idx==0)
            scales.append(scale)
        scales = [[idx,idx+1] for idx in range(len(crops)-1) if scales[idx]==self.maxScale and scales[idx+1]==self.maxScale]
        cnt = len(scales)
        idx = 0
        reduced = False
        while idx < cnt:
            box = PageParser.mergeBoxes(crops[scales[idx][0]], crops[scales[idx][1]])
            _, _, _,  (scale, _, _) = self.getTransformation(box, idx==0)
            if scale == self.maxScale:
                reduced = True
                crops[scales[idx][0]] = box
                crops[scales[idx][1]] = None
                if [scales[idx][1],scales[idx][1]+1] in scales:
                    cnt-=1
                    scales[idx][1]=scales[idx+1][1]
                    del(scales[idx+1])
                else:
                    idx+=1
            else:
                idx+=1
        if reduced:
            try:
                while True:
                    crops.remove(None)
            except ValueError:
                pass


    def processTrimmed(self, page, pageno, crops, maxScale):
        self.maxScale = maxScale
        self.reduceCrops(crops)
        self.device.setCropBoxes(crops)
        self.interpreter.process_page(page, len(crops))
        for idx in range(len(crops)):
            self.fo.write("\n#################    %d-%d-%d     #####################\n"%(self.outpageno+1, pageno+1, idx+1))
            startpos = self.fo.tell()
            self.fo.write(self.interpreter.filteredstreams[idx].getvalue())
            endpos = self.fo.tell()
            isRotated, ctm, clipBox,  (scale, w1, h1) = self.getTransformation(crops[idx], idx==0)
            self.scales.append({'rotated':isRotated, 'H':self.H, 'W':self.W, 
                           'ctm':ctm, 'scale':scale, 'idx':idx, 'box':crops[idx], 
                           'inpageno':pageno, 'opageno':self.outpageno, 'streamoff':startpos, 'streamlen':endpos-startpos})
            self.outpageno+=1

    def getTransformation(self, c, isFirst):
        H = self.H
        W = self.W
        w = c[2]-c[0]
        h = c[3]-c[1]
        def sgn2(a,b):
            c = a<b
            return 1*c-1*(not c)
        def sgn(a):
            c = a>0
            return 1*c-1*(not c)
        
        def cmp1(x,y):
            if x[1]==y[1]:
                return -x[0]+y[0]
            return x[1]-y[1]
        def cmp2(x,y):
            return sgn(cmp1(x,y))
        
        B = [(W,H),(W,H),(H,W),(H,W)]
        C = [W/(w+2),H/(h+2),W/(h+2),H/(w+2)]
        C = [min(x,self.maxScale) for x in C]
        C = [(i,s) for i,s in enumerate(C) if w*s <= B[i][0] and h*s <=B[i][1]]
        C.sort(cmp=cmp2, reverse=True)
        D=[(i,s,(B[i][0]/s-w)/2.0, (B[i][1]/s-h)/2.0) for i,s in C]
        D = D[0]
        isRotated = D[0]<=1
        w_left =h_right= D[2]
        h_dn = h_up = D[3]
        scale = D[1]
        x0= c[0]-w_left
        y0= c[1] - h_dn
        x1= c[2]+w_left
        y1= c[3] + h_up
        h1 = h+h_up+h_dn
#        if origScale != 0 and origScale > self.maxScale and not isRotated:
#            isRotated = True
        if not isRotated:
            ctm = (scale,0.0,0.0,scale, -x0*scale,-y0*scale)
            clipBox = (x0*scale, y0*scale, x1*scale, y1*scale)
        else:
            #ctm = (0.0, scale, -scale, 0.0, y0*scale + (c[3]-c[1]+h_dn)*scale, -x0*scale)
            clipBox = (y0*scale, x0*scale, y1*scale, x1*scale)
            ctm = (0.0, scale, -scale, 0.0, y0*scale + h1*scale, -x0*scale)
        return (isRotated, ctm, clipBox,(scale, W,H))
        
    def getTransformationFine(self, c, isFirst):
        isRotated = True
        H = self.H
        W = self.W
        w = c[2]-c[0]
        h = c[3]-c[1]
        w1=w
        h1=h
        h_up=h_dn=w_left=0.0
        if w >= h:
            if W > H:
                scale = W/w
                if h*scale > H:
                    #isRotated = False
                    scale = H/h
                    w1=h1*W/H
                    w_left = (w1 -w)/2.0
                else:
                    h1=w1*H/W
                    if isFirst:
                        h_up = h1 -h
                    else:
                        h_dn = h1 -h
                    h_up = h_dn = (h1-h)/2.0
            else:
                raise Exception('unimplemented W<H w>h')
        else:
            if W>H:
                isRotated = False
                scale = W/h
                if w*scale > H:
                    scale = H/w
                    h1=w1*W/H
                    if isFirst:
                        h_up = h1 - h
                    else:
                        h_dn = h1 - h
                    h_up = h_dn = (h1-h)/2.0
                else:
                    w1=h1*H/W
                    w_left = (w1 - w)/2.0
            else:
                raise Exception('unimplemented W<H h>w')

        x0= c[0]-w_left
        y0= c[1] - h_dn
        x1= c[2]+w_left
        y1= c[3] + h_up
        if scale > self.maxScale and not isRotated:
            isRotated = True
            
        scale = min(scale, self.maxScale)
        if not isRotated:
            ctm = (scale,0.0,0.0,scale, -x0*scale,-y0*scale)
            clipBox = (x0*scale, y0*scale, x1*scale, y1*scale)
        else:
            #ctm = (0.0, scale, -scale, 0.0, y0*scale + (c[3]-c[1]+h_dn)*scale, -x0*scale)
            clipBox = (y0*scale, x0*scale, y1*scale, x1*scale)
            ctm = (0.0, scale, -scale, 0.0, y0*scale + h1*scale, -x0*scale)
        return (isRotated, ctm, clipBox,(scale, W,H))
        
    def endProcess(self):
        self.fo.close()
        return self.scales

        


        
        