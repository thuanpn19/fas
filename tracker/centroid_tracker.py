from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np


class CentroidTracker():
    def __init__(self, maxDisappeared=30):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.originRects = OrderedDict()
        self.disappeared = OrderedDict()

        self.maxDisappeared = maxDisappeared
    

    def register(self, centroid, rect):
        self.originRects[self.nextObjectID] = rect
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        del self.originRects[objectID]
        del self.objects[objectID]
        del self.disappeared[objectID]

    def get_id(self, rect):
        (x, y, eX, eY) = rect
        cX = ((x + eX) / 2.0)
        cY = ((y + eY) / 2.0)

        objectIDs = list(self.objects.keys())
        objectCentroids = list(self.objects.values())
        
        D = dist.cdist(np.array(objectCentroids), [(cX, cY)])

        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]
        objectID = None

        for (row, col) in zip(rows, cols):
            objectID = objectIDs[row]
            break
        return objectID

    def update(self, rects):
        new_register = False
        if(len(rects) == 0):
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                # print(self.disappeared[objectID])
                
                if(self.disappeared[objectID] > self.maxDisappeared):
                    self.deregister(objectID)
            return self.objects, new_register
        
        inputCentroids = np.zeros((len(rects), 2), dtype="int")

        for(i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        if(len(self.objects) == 0):
            for i in range(0, len(inputCentroids)):
                centroid = inputCentroids[i]
                rect = rects[i]
                self.register(centroid, rect)
                new_register = True
        
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = dist.cdist(np.array(objectCentroids), inputCentroids)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):

                if row in usedRows or col in usedCols:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.originRects[objectID] = rects[col]
                self.disappeared[objectID] = 0

                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:

                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1

                    if self.disappeared[objectID] > self.maxDisappeared:
                        self.deregister(objectID)

            else:

                for col in unusedCols:
                    centroid = inputCentroids[col]
                    rect = rects[col]
                    self.register(centroid, rect)
                    new_register = True
            
            if D[0][0] > 50:
                new_register = True

        return self.objects, new_register