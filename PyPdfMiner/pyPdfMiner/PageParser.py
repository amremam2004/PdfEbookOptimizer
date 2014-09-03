'''

@author: aemam
'''
from pdfminer.layout import  LTAnno, LTChar, LTCurve, LTTextLine, LTFigure, LTImage
from operator import itemgetter    
import copy
class PageParser(object):
    def __init__(self, layout, MaxSplit, W, H, trimboxes=None, exclude=False, pagebox=None):
        self.pageObjs=[]
        self.MaxSplit = MaxSplit
        self.W = W
        self.H = H
        self.combinedLines = []
        self.layout = layout
        self.sizes =None
        self.crops = None
        self.trimboxes = trimboxes
        self.exclude = exclude
        self.pagebox=pagebox
        if self.trimboxes is not None and pagebox is not None and len(trimboxes) > 0 and trimboxes[0] is not None:
            if pagebox[0] >= trimboxes[0][2] or pagebox[2] <= trimboxes[0][0] or pagebox[1] >= trimboxes[0][3] or pagebox[3] <= trimboxes[0][1]:
                for i in range(len(trimboxes)):
                    self.trimboxes[i] = [pagebox[0] + trimboxes[i][0], pagebox[1] + trimboxes[i][1], pagebox[0] + trimboxes[i][2],pagebox[1] + trimboxes[i][3]]
        else:
            self.trimboxes = [pagebox]
            
                 
                
            
    
    def InsideBox(self, x):
        trimboxes = self.trimboxes
        if isinstance(x, LTCurve):
            pts = filter(lambda v:not(v[0]>=self.pagebox[2] or v[0]<=self.pagebox[0] or v[1]>=self.pagebox[3] or v[1]<=self.pagebox[1]), x.pts)
            if trimboxes != None and len(trimboxes) > 0:
                if self.exclude:
                    pass
                    #pts = filter(lambda v:not(v[0]>=self.pagebox[2] or v[2]<=self.pagebox[0] or v[1]>=self.pagebox[3] or v[3]<=self.pagebox[1]), x.pts)
                else:
                    pts = filter(lambda v:not(v[0]>=trimboxes[0][2] or v[0]<=trimboxes[0][0] or v[1]>=trimboxes[0][3] or v[1]<=trimboxes[0][1]), pts)
            if len(pts)==0:
                return False
        bbox = x.bbox
        if bbox[0]>=self.pagebox[2] or bbox[2]<=self.pagebox[0] or bbox[1] >= self.pagebox[3] or bbox[3]<=self.pagebox[1]:
            return False
        #if not isinstance 
        bbox = self.boundToPageRect(bbox)
        if isinstance(x, LTFigure):
            fig = 1
            fig = fig
        else:
            fig = 0
        if trimboxes == None or len(trimboxes) == 0:
            return True
        if not self.exclude:
            result = False
            for trimbox in trimboxes:
                if isinstance(x, LTCurve):
                    inside = filter(lambda v:not(v[0]>=trimbox[2] or v[0]<=trimbox[0] or v[1]>=trimbox[3] or v[1]<=trimbox[1]), pts)
                    result = result or len(inside)>0                
                else:
                    result = result or not(bbox[0]>=trimbox[2] or bbox[2]<=trimbox[0] or bbox[1]>=trimbox[3] or bbox[3] <=trimbox[1])
                if result:
                    break
        else:
            result = True
            for trimbox in trimboxes:
                if isinstance(x,LTCurve):
                    outside = filter(lambda v:(v[0]>=trimbox[2] or v[0]<=trimbox[0] or v[1]>=trimbox[3] or v[1]<=trimbox[1]), pts)
                    result = result and len(outside)!=0                
                else:
                    result = result and not (bbox[0] >= trimbox[0] and bbox[2] <=trimbox[2] and bbox[1] >= trimbox[1] and bbox[3] <= trimbox[3])
                if not result:
                    break
        return result
                
    def process(self):
        self.parseObjs(self.layout)
        pageLines =[x for x in self.pageObjs 
                    if type(x).__name__ not in ['LTPage', 'LTTextGroupLRTB', 'LTTextBoxHorizontal'] #, 'LTFigure']
                    and (type(x).__name__ != 'LTImage' or (x.srcsize != None and x.srcsize != (1,1)))
                    and (x.height>0 or x.width > 0)]
        if self.trimboxes !=None:
            pageLines = [x for x in pageLines if self.InsideBox(x)]
            
        pageLines = list(set(pageLines))
        sortedPageLines = sorted(pageLines, cmp = lambda x,y: int(-PageParser.cmpItems(x,y)))
        if sortedPageLines == None or len(sortedPageLines) == 0:
            return {'crops':None, 'sortedLines': None, 'combinedLines':None}
        sortedPageLines = self.combineTouchingCurves(sortedPageLines)
        self.combinedLines, self.combinedLinesBoxes = self.combineLines(sortedPageLines)
        self.nLines = len(self.combinedLines)
        if self.nLines <= self.MaxSplit +1:
            self.crops = self.combinedLines
        else:
            self.sizes = [[False]*self.nLines for _ in range(self.nLines)]
            self.buildMatrix()
        sortedPageBoxes = [x for x in sortedPageLines]    
        return {'crops':self.crops, 'sortedLines': sortedPageBoxes, 'combinedLines':self.combinedLines}

    def mergeCrops(self):
        if len(self.crops) <=1:
            return
        moreMege = True
        while moreMege:
            moreMege = False
            for i in range(len(self.crops)-1):
                c1 = self.crops[i]
                c2 = self.crops[i+1]
                s1 = self.getSizeAdjustedH(c1)
                s2 = self.getSizeAdjustedH(c2)
                m = self.mergeBoxes(c1, c2)
                s3 = self.getSizeAdjustedH(m)
                if s3 == s1 or s3 == s2:
                    self.crops[i]=m
                    del(self.crops[i+1])
                    moreMege = True
                    break
        
    def buildMatrix(self):
        self.buildLevel0()
        self.sizesAdjusted = copy.deepcopy(self.sizes)
        self.filterLevel0()
        self.findMinCache = [[False]*(self.MaxSplit +1) for _ in range(self.nLines)]
        result = self.FindMin(0, self.MaxSplit)
        def cmpResults(x,y):
            a=x[0]
            b=y[0]
            if a[0] != b[0]:
                return a[0] - b[0]
            else:
                return a[1] - b[1]
                        
        result = sorted(result, cmp = lambda x,y: int(cmpResults(x,y)))
        self.crops = [x[2] for x in result]

        
        
        
    def buildLevel0(self):
        sizes = self.sizes
        try:
            combinedLines = self.combinedLines
            for k in range(self.nLines-1,-1,-1):
                sizes[k][k]=combinedLines[k]
            for i in range(1,self.nLines):
                for k in range(self.nLines-i):
                    sizes[k][k+i] = PageParser.mergeBoxes(sizes[k][k+i-1], sizes[k+1][k+i])
        except Exception, e:
            print e
            
    @staticmethod
    def isTouching(x,y):
        return not (x[0]>y[2] or y[0] > x[2] or x[1] > y[3] or y[1] > x[3] )       
      
    @staticmethod
    def isIntersecting(x,y):
        return not (x[0]>=y[2] or y[0] >= x[2] or x[1] >= y[3] or y[1] >= x[3] )       

    def boundToPageRect(self, bbox):
        return (max(bbox[0],self.pagebox[0]),max(bbox[1],self.pagebox[1]),min(bbox[2],self.pagebox[2]),min(bbox[3],self.pagebox[3]))
        
    def combineTouchingCurves(self, sortedPageLines): 
            fullCurveIdxs = [ i for i in range(len(sortedPageLines)) if type(sortedPageLines[i]).__name__ in ['LTImage', 'LTCurve', 'LTLine', 'LTRect']]
            if len(fullCurveIdxs) == 0:
                return [self.boundToPageRect(x.bbox) for x in sortedPageLines]
            noncurves = [[i,self.boundToPageRect(sortedPageLines[i].bbox)]  for i in range(len(sortedPageLines)) if i not in fullCurveIdxs]
            curves=[[i,self.boundToPageRect(sortedPageLines[i].bbox)] for i in fullCurveIdxs]


            while True:
                for i in range(len(curves) - 1):
                    if curves[i] == None :
                        continue
                    for j in range(i+1, len(curves)):
                        if curves[j] == None:
                            continue
                        if PageParser.isTouching(curves[i][1], curves[j][1]):
                            curves[i][1] = PageParser.mergeBoxes(curves[i][1], curves[j][1])
                            curves[j] = None
                prevLen = len(curves)
                curves = [u for u in curves if u != None]
                newLen = len(curves)
                if(newLen == prevLen):
                    break
            
            for b in range(len(curves)):
                x = curves[b][1]
                if not (abs(x[0] -x[2]) > 2 and abs(x[1]-x[3]) > 2):
                    continue
                for u in range(len(noncurves)):
                    if noncurves[u] == None:
                        continue
                    if PageParser.isTouching(curves[b][1], noncurves[u][1]):
                        curves[b][1] = PageParser.mergeBoxes(curves[b][1], noncurves[u][1])
                        noncurves[u] = None
                               
            while True:
                for i in range(len(curves) - 1):
                    if curves[i] == None :
                        continue
                    for j in range(i+1, len(curves)):
                        if curves[j] == None:
                            continue
                        if PageParser.isTouching(curves[i][1], curves[j][1]):
                            curves[i][1] = PageParser.mergeBoxes(curves[i][1], curves[j][1])
                            curves[j] = None
                prevLen = len(curves)
                curves = [u for u in curves if u != None]
                newLen = len(curves)
                if(newLen == prevLen):
                    break
            noncurves = [ x for x in noncurves if x != None]
                    
            combined = sorted(curves + noncurves, key=itemgetter(0))
            combined = [x[1] for x in combined]
            return combined
        
    def combineLines(self, sortedPageLines):
        combinedLines = []
        combinedLinesBoxes = []
        prevBox = sortedPageLines[0]
        prevIdx = 0
        combinedLines.append(prevBox)
        combinedLinesBoxes.append([prevBox])
        for idx in range(1, len(sortedPageLines)):
            box = sortedPageLines[idx]
            try:
                if (prevBox[1] <= box[1] and prevBox[3] >=box[3]) or (box[1] <= prevBox[1]  and box[3] >=prevBox[3]):
                    prevBox = PageParser.mergeBoxes(box, prevBox)
                    combinedLines[prevIdx] = prevBox
                    combinedLinesBoxes[prevIdx].append(box)
                else:
                    prevIdx += 1
                    prevBox = box
                    combinedLines.append(prevBox)
                    combinedLinesBoxes.append([prevBox])
            except Exception, _:
                print prevBox
                print box
                raise
        return combinedLines, combinedLinesBoxes
    
    def parseObjs(self, item, addChar=False):
        if item == None:
            return
        if isinstance(item, LTCurve):
            item = item
        addObj = True
        if (not addChar and isinstance(item, LTChar)) or isinstance(item, LTAnno):
            addObj = False
        #if isinstance(item, LTCurve) and (not hasattr(item, 'linewidth') or item.linewidth == 0):
        #   addObj = False
                
        if isinstance(item, LTFigure):
            addObj = False
            box = None
            if hasattr(item, '_objs') and item._objs != None and len(item._objs)>0:
                for o in item._objs:
                    if isinstance(o, LTImage)  and (o.srcsize == None or o.srcsize == (1,1)):
                        continue
                    addObj = True
                    box = PageParser.mergeBoxes(box, o.bbox)
            if hasattr(item, 'groups') and item.groups != None and len(item.groups)>0:
                for o in item.groups:
                    if isinstance(o, LTImage)  and (o.srcsize == None or o.srcsize == (1,1)):
                        continue
                    addObj = True
                    box = PageParser.mergeBoxes(box, o.bbox)
            if addObj:
                item.bbox = box
                self.pageObjs.append(item)
            return
            
        if addObj: #if item not in pageObjs:
            self.pageObjs.append(item)
        if hasattr(item, 'groups') and item.groups != None:
            for o in item.groups:
                self.parseObjs(o)
        if hasattr(item, '_objs') and item._objs != None:
            for o in item._objs:
                self.parseObjs(o, not isinstance(item, LTTextLine))

    @staticmethod
    def cmpItems1(a,b):
        if a.y1 != b.y1:
            return a.y1 - b.y1
        if a.y0 != b.y0:
            return a.y0 - b.y0
        if a.x0 != b.x0:
            return a.x0 - b.x0
        return a.x1 - b.x1

    @staticmethod
    def cmpItems(a,b):
        i = PageParser.cmpItems1(a,b)
        if i > 0:
            return 1
        elif i< 0:
            return -1
        return 0

    @staticmethod
    def mergeBoxes(a,b):
        if a == None:
            return b
        if b == None:
            return a
        return (min(a[0],b[0],a[2],b[2]), min(a[1],b[1],a[3],b[3]), max(a[0],b[0],a[2],b[2]), max(a[1],b[1],a[3],b[3]))

    @staticmethod
    def getSize(b):
        return abs(b[0]-b[2])*abs(b[1]-b[3])
    

    def getSizeAdjustedH(self, b):
        w = abs(b[0]-b[2])
        h = abs(b[1]-b[3])
        h = max(h, w*self.H/self.W)
        return w*h

    def getSizeAdjusted(self, b, isFirstOrLast, isSingleObject):
        W = self.W
        H = self.H
        w = abs(b[0]-b[2])
        h = abs(b[1]-b[3])
        w = max(w, h*self.W/self.H)
        return w*h
        if W < H:
            raise Exception('unsupported')
        if isFirstOrLast:
            if h <= w*H/W:
                return w*h
            else:
                w = max(w, h*self.W/self.H)
                return w*h
        if  not isSingleObject:
            w = max(w, h*self.W/self.H)
            return w*h
            
        w = max(w, h*self.W/self.H)
        return w*h
        return min([x for x in (w**2*W/H,w**2*H/W,h**2*W/H,h**2*H/W) if x >=w*h])
    
    
    @staticmethod
    def cmpRectUp(a,b):
        return a[1] - b[1]

    @staticmethod
    def cmpRectDn(a,b):
        return a[3] - b[3]

    @staticmethod
    def findClosest(box, boxes, up):
        d=[x for x in boxes if 
           (x[0]>box[0] and x[0]<box[2]) or 
           (x[2] > box[0] and x[2]< box[2]) or 
           (box[0] > x[0] and box[0] < x[2]) or 
           (box[2] > x[0] and box[2] < x[2])]
        if len(d)== 0:
            return None
        if up:
            return d[0][1]-box[3]
        else:
            return box[1]-d[0][3]

    def filterLevel0(self):
        nlines = self.nLines
        W=self.W
        H=self.H
        sizes = self.sizesAdjusted
        for i in range(0,nlines):
            for k in range(nlines-i):
                #if k==0 or k+i == nlines -1:
                #    continue
   
                b = list(sizes[k][k+i])
                w=b[2]-b[0]
                h=b[3]-b[1]
                if  i != 0:
                    if w < h*W/H:
                        w1 = h*W/H
                        df = (w1-w)
                        b[0]-=df
                        b[2]+=df
                        sizes[k][k+i] = b
        for i in range(0, nlines):
            if sizes[i][i] != None and sizes[i][i]!=False:
                b = list(sizes[i][i])
                h = b[3] - b[1]
                if h == 0:
                    sizes[i][i]=False
                
                    
                    


    def FindMin(self, I, splits):
        if self.findMinCache[I][splits] != False:
            return list(self.findMinCache[I][splits])
        minsizes1=[]
        sizes=self.sizes
        sizesAdjusted = self.sizesAdjusted
        nlines = self.nLines
        if splits==0:
            minsizes1.append([[(I,nlines-1),sizes[I][nlines-1],sizesAdjusted[I][nlines-1]]])
            self.findMinCache[I][splits] = minsizes1[0]
            return list(self.findMinCache[I][splits])
        for i in range(I, nlines):
            if I == 0 and i ==9:
                i=9
            if sizesAdjusted[I][i] == False:
                continue
            if i+1 < nlines:
                C = sizesAdjusted[i+1]
                if not any(C):
                    continue
                
                remsize = self.FindMin(i+1, splits-1)
                if remsize == None or len(remsize) == 0:
                    continue
                if len(remsize) > splits+1:
                    remsize = remsize
                remsize.insert(0,[(I,i),sizes[I][i], sizesAdjusted[I][i]])
                minsizes1.append(remsize)
                i=i
            else:
                minsizes1.append([[(I,i),sizes[I][i], sizesAdjusted[I][i]]])
        if len(minsizes1) == 0:
            self.findMinCache[I][splits] = None
            return self.findMinCache[I][splits]
        boxsizes = []
        for (i,b) in enumerate(minsizes1):
            size = 0
            for id1, a, aA in b:
                if False:
                    w=a[2]-a[0]
                    h=a[3]-a[1]
                    if (h <= w*self.H/self.W) or id1[0] !=id1[1]:
                        size += (a[2]-a[0])*(a[3]-a[1])
                    else:
                        size += (aA[2]-aA[0])*(aA[3]-aA[1])
                size += (aA[2]-aA[0])*(aA[3]-aA[1])
            boxsizes.append(size)

        def width1(i):
            a=self.combinedLines[i]
            return (a[2]-a[0])
            
        idxes = sorted(range(len(minsizes1)),key=boxsizes.__getitem__)
            
            
            
        self.findMinCache[I][splits] = minsizes1[idxes[0]]
        return list(self.findMinCache[I][splits])
