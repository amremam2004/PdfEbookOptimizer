'''

@author: aemam
'''

class SelectedPages(object):
    def __init__(self, selectedpages):
        self.selectedpages=[]
        if selectedpages == None or len(selectedpages) ==0:
            return
        ranges=selectedpages.split(',')
        for r in ranges:
            r=r.split('-')
            if len(r)==1:
                self.selectedpages.append([int(r[0])])
            elif r[0]=='':
                self.selectedpages.append([None, int(r[1])])
            elif r[1]=='':
                self.selectedpages.append([int(r[0]),None])
            else:
                self.selectedpages.append([int(r[0]),int(r[1])])
            
    def isInRange(self, pageNo):
        inRange=False
        if len(self.selectedpages)==0:
            inRange = True
        else:
            for r in self.selectedpages:
                if len(r)==1:
                    if r[0]==pageNo:
                        inRange=True
                elif r[0] is None:
                    if pageNo<=r[1]:
                        inRange=True
                elif r[1] is None:
                    if pageNo>=r[0]:
                        inRange=True
                else:
                    if (pageNo >= r[0]) and (pageNo <=r[1]):
                        inRange=True
                if inRange:
                    break
        return inRange
    def __contains__(self, selectedpages):
        s= SelectedPages(selectedpages)
        inRange = True
        for r in s.selectedpages:
            if len(r)==1:
                inRange = self.isInRange(r[0])
            elif r[0] is None:
                inRange = self.isInRange(r[1])
            elif r[1] is None:
                inRange = self.isInRange(r[0])
            else:
                inRange = self.isInRange(r[0]) and self.isInRange(r[1])
            if not inRange:
                break
        return inRange
    
    def getEndPage(self, NumOfPages):
        maxPage = -1
        if len(self.selectedpages)==0:
            maxPage = NumOfPages
        else:
            maxPage = -1
            for r in self.selectedpages:
                if len(r)==1:
                    if maxPage < r[0]:
                        maxPage = r[0]
                elif r[0] is None:
                    if maxPage < r[1]:
                        maxPage = r[1]
                elif r[1] is None:
                    maxPage = NumOfPages
                else:
                    if maxPage < r[1]:
                        maxPage = r[1]
        return maxPage


 