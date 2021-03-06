import sys, math
import numpy as np
from trackml.dataset import load_event
from dataset_path import get_path

class Voxels:
    def __init__(self, points, numBins=100):
        self.numBins = numBins
        self.numPoints = len(points)
        self.xIndex = points.columns.get_loc('x')
        self.yIndex = points.columns.get_loc('y')
        self.zIndex = points.columns.get_loc('z')

        self.minX = points.x.min()
        self.minY = points.y.min()
        self.minZ = points.z.min()
        self.maxX = points.x.max()
        self.maxY = points.y.max()
        self.maxZ = points.z.max()

        self.xRange = self.maxX - self.minX
        self.yRange = self.maxY - self.minY
        self.zRange = self.maxZ - self.minZ

        self.bins = [[[[] for i in range(numBins)] for j in range(numBins)] for k in range(numBins)]
        self.usedIndices = set()
        
        i, j, k = self.getBinIndices(points.x.values, points.y.values, points.z.values)
        raw = points.values
        total = self.numPoints
        percent = int(total / 100)
        print("Create voxels... ", end="")
        for idx in range(self.numPoints):
            if idx % percent == 0: print("\rCreate voxels..." + str(int(100*idx / total)) + "%", end="")
            self.usedIndices.add((i[idx], j[idx], k[idx]))
            self.bins[i[idx]][j[idx]][k[idx]].append(raw[idx])
            # self.bins[i[idx]][j[idx]][k[idx]].append(points.iloc[idx])
        print("\rCreate voxels... 100%")

    def getBinIndices(self, x, y, z):
        i = np.floor((self.numBins-1) * (x - self.minX) / self.xRange).astype(int)
        j = np.floor((self.numBins-1) * (y - self.minY) / self.yRange).astype(int)
        k = np.floor((self.numBins-1) * (z - self.minZ) / self.zRange).astype(int)

        i = np.maximum(0, i)
        i = np.minimum(self.numBins-1, i)
        j = np.maximum(0, j)
        j = np.minimum(self.numBins-1, j)
        k = np.maximum(0, k)
        k = np.minimum(self.numBins-1, k)

        return i, j, k

    def findClosestPoint(self, x, y, z):
        i, j, k = self.getBinIndices(x, y, z)
        window = 1
        high = window + 1
        neighboring_points = []
        while len(neighboring_points) == 0:
            for ii in range(max(0,i-window), min(i+high,self.numBins)):
                for jj in range(max(0,j-window), min(j+high,self.numBins)):
                    for kk in range(max(0,k-window), min(k+high,self.numBins)):
                        neighboring_points.extend(self.bins[ii][jj][kk])
            window += 1
            high = window + 1

        min_dist = sys.maxsize
        closest_point = neighboring_points[0]

        neighboring_points = np.asarray(neighboring_points)
        distances = np.sqrt((x-neighboring_points[:,1])**2 + (y-neighboring_points[:,2])**2 + (z-neighboring_points[:,3])**2)
        min_idx = np.argmin(distances)

        return neighboring_points[min_idx]


    def getMaxBinCount(self):
        maxBinCount = 0
        for idx in self.usedIndices:
            if len(self.bins[idx[0]][idx[1]][idx[2]]) > maxBinCount:
                maxBinCount = len(self.bins[idx[0]][idx[1]][idx[2]])
        return maxBinCount

    def getNumSurrounding(self, r, x, y, z):
        nhits = 0
        rReached = False
        i, j, k = self.getBinIndices(x, y, z)
        i_window = int(r / (self.xRange / self.numBins))+1
        j_window = int(r / (self.yRange / self.numBins))+1
        k_window = int(r / (self.zRange / self.numBins))+1
        possible_points = []
        for ii in range(max(0,i-i_window), min(i+i_window+1,self.numBins)):
            for jj in range(max(0,j-j_window), min(j+j_window+1,self.numBins)):
                for kk in range(max(0,k-k_window), min(k+k_window+1,self.numBins)):
                    possible_points.extend(self.bins[ii][jj][kk])

        if (len(possible_points) == 0):
            return 0

        point = np.asarray([x, y, z])
        possible_points = np.asarray(possible_points)
        diff = point - possible_points[:,1:4]
        square = np.square(diff)
        sum_of_squares = np.sum(square, axis=1)
        bool_array = np.sqrt(sum_of_squares) < r

        return np.sum(bool_array)


# test
if __name__ == "__main__":
    path_to_dataset = get_path()
    event_path = "event000001052"
    hits, cells, particles, truth = load_event(path_to_dataset + event_path)

    hit_voxels = Voxels(hits, 300)

    print(hit_voxels.getMaxBinCount())

    #for i in range(100):
    #    print("closest point to ", hits.x.values[i], hits.y.values[i], hits.z.values[i])
    #    print(hit_voxels.findClosestPoint(hits.x.values[i], hits.y.values[i], hits.z.values[i]))

    print("number of points < 50 away from the origin -- test method()", hit_voxels.getNumSurrounding(50, 0, 0, 0))


    dists = (np.linalg.norm(hits[['x','y','z']].values, axis=1))

    print("number of points < 50 away from origin -- verify", np.sum(dists < 50))
    print("min dist", np.amin(dists))
