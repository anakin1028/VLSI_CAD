import pdb
import re
import heapq
import copy
import time
class Maze:
    def __init__(self, NumX, NumY, bendPenalty, viaPenalty):
        self.mazeMatrix = {(x,y):0 for x in range(NumX) for y in range(NumY)}
        self.bendPenalty = bendPenalty
        self.viaPenalty = viaPenalty
        self.NumX = NumX
        self.NumY = NumY

class Grid:
    def __init__(self, cost, coordX, coordY, Reach, Layer, PathCost, Pred):
        self.cost = cost
        self.coordX = coordX
        self.coordY = coordY
        self.Reach = Reach
        self.Layer = Layer
        self.PathCost = PathCost
        self.Pred = Pred
    def resetGridObj(self):
        self.coordX = 0
        self.coordY = 0
        self.Reach = 0
        self.PathCost = 0
        self.Pred = 0
class Net:
    def __init__(self, netId, pin1Layer, pin2Layer, pin1_X, pin1_Y, pin2_X, pin2_Y):
        self.netId = netId
        self.pin1Layer = pin1Layer
        self.pin2Layer = pin2Layer
        self.pin1_X = pin1_X
        self.pin1_Y = pin1_Y
        self.pin2_X = pin2_X
        self.pin2_Y = pin2_Y
def ReadInput(gridFilePath):
    gridFile = open(gridFilePath, "r")
    line = gridFile.readline().split("\n")[0]
    lineList = line.split(" ")
    numCol = int(lineList[0])
    numRow = int(lineList[1])
    bendPenalty = int(lineList[2])
    viaPenalty = int(lineList[3])
    MazeObj1 = Maze(numCol, numRow, bendPenalty, viaPenalty)
    MazeObj2 = Maze(numCol, numRow, bendPenalty, viaPenalty)
    for i in range(2):
        if i == 0:
            MazeObj = MazeObj1
        else:
            MazeObj = MazeObj2
        for j in range(numRow):
            line = gridFile.readline()
            lineList = re.split("\s+", line)
            for k in range(numCol):
                cost = int(lineList[k+1])
                MazeObj.mazeMatrix[(k,j)] = Grid(cost, 0, 0, 0, i+1, 0, 0)
    return MazeObj1, MazeObj2

def buildNetList(NetListFilePath):
    netFile = open(NetListFilePath, "r")
    netNum = int(netFile.readline().split("\n")[0])
    netList = []
    for i in range(netNum):
        line = netFile.readline()
        line = line.split("\n")[0]
        lineList = re.split("\W+", line)
        if lineList[0]=='':
            netId = int(lineList[1])
            j = 1
        else:
            netId = int(lineList[0])
            j = 0
        pin1Layer = int(lineList[j+1])
        pin1_X = int(lineList[j+2])
        pin1_Y = int(lineList[j+3])
        pin2Layer = int(lineList[j+4])
        pin2_X = int(lineList[j+5])
        pin2_Y = int(lineList[j+6])
        netObj = Net(netId, pin1Layer, pin2Layer, pin1_X, pin1_Y, pin2_X, pin2_Y)
        netList.append(netObj)
    return netList

def heapPush(h, GridObj):
    heapq.heappush(h, (GridObj.PathCost, GridObj))

def getSourceCell(mazeObj1, mazeObj2, netObj):
    sourceLayer = netObj.pin1Layer
    sPinX = netObj.pin1_X
    sPinY = netObj.pin1_Y
    if sourceLayer == 1:
        sourceGrid = mazeObj1.mazeMatrix[(sPinX,sPinY)]
        sourceGrid.Layer = 1
    else:
        sourceGrid = mazeObj2.mazeMatrix[(sPinX,sPinY)]
        sourceGrid.Layer = 2
    sourceGrid.coordX = sPinX
    sourceGrid.coordY = sPinY
    sourceGrid.PathCost = sourceGrid.cost
    sourceGrid.Reach = 1
    sourceGrid.Pred = "Source"
    return sourceGrid

def isTarget(gridObj, netObj):
    if gridObj.coordX == netObj.pin2_X and gridObj.coordY == netObj.pin2_Y:
        if gridObj.Layer == netObj.pin2Layer:
            return 1
        else:
            return 0
    else:
        return 0
    
def cleanUp(footPathList,pathObjList):
    resetList = list(set(footPathList) - set(pathObjList))
    for Item in resetList:
        Item.resetGridObj()
    #for Item in footPathList:
    #    if list(set([Item]) & set(pathObjList))==[]:
    #        Item.resetGridObj()
    
    for Item in pathObjList:
        Item.cost = -1

def findNbr(mazeObj1, mazeObj2, gridObj):
    nbrCellList = []
    if gridObj.Layer == 1:
        mazeObj = mazeObj1
    else:
        mazeObj = mazeObj2
    llx = 0
    lly = 0
    urx = mazeObj.NumX - 1
    ury = mazeObj.NumY - 1
    if gridObj.coordX > 0:
        eastNbr = mazeObj.mazeMatrix[(gridObj.coordX-1,gridObj.coordY)]
        if eastNbr.Reach == 0 and eastNbr.cost!=-1:
            eastNbr.coordX = gridObj.coordX - 1
            eastNbr.coordY = gridObj.coordY
            nbrCellList.append(eastNbr)
    if gridObj.coordX < urx:
        westNbr = mazeObj.mazeMatrix[(gridObj.coordX+1,gridObj.coordY)]
        if westNbr.Reach == 0 and westNbr.cost!=-1:
            westNbr.coordX = gridObj.coordX + 1
            westNbr.coordY = gridObj.coordY
            nbrCellList.append(westNbr)
    if gridObj.coordY > 0:
        southNbr = mazeObj.mazeMatrix[(gridObj.coordX, gridObj.coordY-1)]
        if southNbr.Reach == 0 and southNbr.cost!=-1:
            southNbr.coordX = gridObj.coordX
            southNbr.coordY = gridObj.coordY - 1
            nbrCellList.append(southNbr)
    if gridObj.coordY < ury:
        northNbr = mazeObj.mazeMatrix[(gridObj.coordX, gridObj.coordY+1)]
        if northNbr.Reach == 0 and northNbr.cost!=-1:
            northNbr.coordX = gridObj.coordX
            northNbr.coordY = gridObj.coordY + 1
            nbrCellList.append(northNbr)
    if gridObj.Layer == 1:
        upNbr = mazeObj2.mazeMatrix[(gridObj.coordX,gridObj.coordY)]
        if upNbr.Reach == 0 and upNbr.cost != -1:
            upNbr.coordX = gridObj.coordX
            upNbr.coordY = gridObj.coordY
            nbrCellList.append(upNbr)
    if gridObj.Layer == 2:
        downNbr = mazeObj1.mazeMatrix[(gridObj.coordX,gridObj.coordY)]
        if downNbr.Reach == 0 and downNbr.cost != -1:
            downNbr.coordX = gridObj.coordX
            downNbr.coordY = gridObj.coordY
            nbrCellList.append(downNbr)
    return nbrCellList

def backTrace(targetCell):
    pathCellList = []
    while targetCell.Pred != "Source":
        pathCellList.append(targetCell)
        targetCell = targetCell.Pred
    pathCellList.append(targetCell)
    return pathCellList

def calBendCost(gridObj, bendPenalty):
    prevObj = gridObj.Pred
    if prevObj.Pred != "Source":
        prev2Obj = prevObj.Pred
    else:
        return 0
    #walk vertically previously
    if prevObj.coordX == prev2Obj.coordX:
        if gridObj.coordX == prevObj.coordX:
            return 0
        else:
            return bendPenalty
    #walk horizantally
    else:
        if gridObj.coordY == prevObj.coordY:
            return 0
        else:
            return bendPenalty

def onOffBlockPin(mazeObj1, mazeObj2, netObj, cost):
    if netObj.pin1Layer == 1:
        mazeObj1.mazeMatrix[(netObj.pin1_X,netObj.pin1_Y)].cost = cost
    else:
        mazeObj2.mazeMatrix[(netObj.pin1_X, netObj.pin1_Y)].cost = cost
    if netObj.pin2Layer == 1:
        mazeObj1.mazeMatrix[(netObj.pin2_X,netObj.pin2_Y)].cost = cost
    else:
        mazeObj2.mazeMatrix[(netObj.pin2_X, netObj.pin2_Y)].cost = cost
        
def RouteSingleNet(mazeObj1, mazeObj2, netObj):
    waveFront = []
    loop = 1
    #Test1
    start_time = time.time()
    sourceGrid = getSourceCell(mazeObj1, mazeObj2,netObj)
    heapPush(waveFront, sourceGrid)
    onOffBlockPin(mazeObj1, mazeObj2, netObj, 1)
    footPathList = []
    print "COST1", time.time() - start_time
    start_time = time.time()
    #print netObj.netId
    while loop == 1:
        if len(waveFront)==0:
            onOffBlockPin(mazeObj1, mazeObj2, netObj, -1)
            cleanUp(footPathList, [])
            return []
        cheapCell = waveFront[0][1]
        footPathList.append(cheapCell)
        #print cheapCell.coordX, cheapCell.coordY
        if isTarget(cheapCell, netObj)==1 :
            print "Find Nbr time", time.time() - start_time
            start_time = time.time()
            pathCellList = backTrace(cheapCell)
            print "FindPathCellList", time.time() - start_time
            start_time = time.time()
            cleanUp(footPathList, pathCellList)
            print "CleanUp", time.time() - start_time
            #pathObjList = copy.deepcopy(pathCellList)
            onOffBlockPin(mazeObj1, mazeObj2, netObj, -1)
            #return pathObjList
            return pathCellList
        nbrCellList = findNbr(mazeObj1, mazeObj2, cheapCell)
        for gridCell in nbrCellList:
            footPathList.append(gridCell)
            gridCell.Reach = 1
            gridCell.Pred = cheapCell
            if cheapCell.Layer == gridCell.Layer:
                pathCost = cheapCell.PathCost + gridCell.cost + calBendCost(gridCell, mazeObj1.bendPenalty) + (abs(cheapCell.coordX-gridCell.coordX)+abs(cheapCell.coordY-gridCell.coordY))
            else:
                pathCost = cheapCell.PathCost + gridCell.cost + mazeObj1.viaPenalty
            gridCell.PathCost = pathCost
        heapq.heappop(waveFront)
        for gridCell in nbrCellList:
            heapPush(waveFront, gridCell)
    
def RouteNet(mazeObj1, mazeObj2, netObjList):
    netPathList = []
    for netObj in netObjList:
        pathObjList = RouteSingleNet(mazeObj1, mazeObj2, netObj)
        netPathList.append(pathObjList)
        #copyNetPathList = copy.deepcopy(netPathList)
    return netPathList

def GenerateOutPut(pathCellList ,outFilePath):
    outFile = open(outFilePath, "w")
    outFile.write(str(len(pathCellList))+"\n")
    for i in range(len(pathCellList)):
        netPathObjList = pathCellList[i]
        netPathObjList = netPathObjList[::-1]
        outFile.write(str(i+1)+"\n")
        if len(netPathObjList)>0:
            tmpLayer = str(netPathObjList[0].Layer)
            for gridObj in netPathObjList:
                layer = str(gridObj.Layer)
                xCoord = str(gridObj.coordX)
                yCoord = str(gridObj.coordY)
                if layer != tmpLayer:
                    outFile.write("3" + " " + xCoord + " " + yCoord + "\n")
                outFile.write(layer + " " + xCoord + " " + yCoord + "\n")
                tmpLayer = layer
        outFile.write("0"+"\n")
    outFile.close()
    
if __name__ == "__main__":
    MazeObj1, MazeObj2 = ReadInput("D:/Users/chientut/Documents/Course/CAD_VLSI/HW/ProgrammingAssignment4Files/mazeRouteGRID.grid")
    netObjList = buildNetList("D:/Users/chientut/Documents/Course/CAD_VLSI/HW/ProgrammingAssignment4Files/mazeRouteNet.nl") 
    pathCellList = RouteNet(MazeObj1, MazeObj2, netObjList)
    GenerateOutPut(pathCellList,"D:/Users/chientut/Documents/Course/CAD_VLSI/HW/ProgrammingAssignment4Files/testOut.txt" )
    
    
