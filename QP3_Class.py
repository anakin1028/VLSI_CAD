import re
import numpy
import pdb
from itertools import permutations
import operator as op

def buildNetToGateDict(inFilePath):
    inFile = open(inFilePath, "r")
    line1 = inFile.readline()
    line1Parse = line1.split(" ")
    gateNumber = int(line1Parse[0])
    netNumber = int(line1Parse[1].split("\n")[0])
    NetToGateDict = {}
    NetToPadDict = {}
    for i in range(gateNumber):
        line = re.match("(.+\d)\W+",inFile.readline()).group(1)
        lineParse = line.split(" ")
        for i in range(len(lineParse)-2):
            netId = int(lineParse[i+2])
            if netId not in NetToGateDict:
                NetToGateDict[netId] = []
            NetToGateDict[netId].append(int(lineParse[0]))
    padNumber = int(inFile.readline())
    for i in range(padNumber):
        line = re.search("(.+\d)", inFile.readline()).group(1)
        lineParse = line.split(" ")
        padId = int(lineParse[0])
        netId = int(lineParse[1])
        xCoord = int(lineParse[2])
        yCoord = int(lineParse[3])
        if netId not in NetToPadDict:
            NetToPadDict[netId] = []
        NetToPadDict[netId].append(padId)
        NetToPadDict[netId].append([xCoord,yCoord])
    inFile.close()
    return (NetToGateDict,NetToPadDict,gateNumber)

            
class Gate:
    def __init__(self, gateId, netObjList):
        self.GateId = gateId
        self.NetObjList = netObjList

class Net:
    def __init__(self,NetId,gateObjList=[],padList=[]):
        self.NetId = NetId
        self.GateObjList = gateObjList
        self.PadList = padList
    def calWeight(self):
        gateOnNetList = self.GateObjList
        padOnNetList = self.PadList
        return 1.0/(len(gateOnNetList)+len(padOnNetList)-1)
    
class Pad:
    def __init__(self, padId, xCoord, yCoord):
        self.padId = padId
        self.xCoord = xCoord
        self.yCoord = yCoord
        
class Placement:
    def __init__(self, GateObjDict={}, NetObjDict={}, PadObjDict={}):
        self.GateObjDict = {}
        self.NetObjDict = {}
        self.PadObjDict = {}
    def buildNetList(self, NetToGateDict, NetToPadDict):
        GateList = []
        PadList = []
        #Map The NetId to NetObject
        NetObjDict = {}
        #Map The GateId to GateObject
        GateObjDict = {}
        #Map The PadId to PadObj
        PadObjDict = {}
        for netId in NetToGateDict:
            netObj = Net(netId, [], [])
            NetObjDict[netId] = netObj
            GateOnNetList = NetToGateDict[netId]
            for GateId in GateOnNetList:
                if GateId not in GateList:
                    GateList.append(GateId)
                    GateObj = Gate(GateId,[])
                    GateObjDict[GateId] = GateObj
                #Remember What Gate Connects
                GateObjDict[GateId].NetObjList.append(netObj)
            netObj.GateObjList = [GateObjDict[gateId] for gateId in GateOnNetList]
        for netId in NetToPadDict:
            PadId = NetToPadDict[netId][0]
            PadCoord = NetToPadDict[netId][1]
            if PadId not in PadList:
                PadList.append(PadId)
                PadObj = Pad(PadId, PadCoord[0], PadCoord[1])
                PadObjDict[PadId] = PadObj
            NetObjDict[netId].PadList.append(PadObjDict[PadId])
        self.GateObjDict = GateObjDict
        self.NetObjDict = NetObjDict
        self.PadObjDict = PadObjDict
    #Build The Gate List in the target Region
    def buildGateList(self, AssignmentFlag):
        if AssignmentFlag == "O":
            GateDict = self.GateObjDict
            GateList = [GateDict[GateId] for GateId in GateDict]
            self.AllGateList = GateList
        elif AssignmentFlag == "L" or AssignmentFlag == "R":
            AllGateList = self.AllGateList
            sortAllGateList = sorted(AllGateList, key = lambda Gate: 100000*Gate.xCoord+Gate.yCoord)
            if AssignmentFlag == "L":
                gateNumber = len(AllGateList)/2
                GateList = sortAllGateList[:len(AllGateList)/2]
            else:
                gateNumber = len(AllGateList) - len(AllGateList)/2
                GateList = sortAllGateList[len(AllGateList)/2:]
        self.GateList = GateList
    def buildConnectMatrix(self):
        #GateList is the GateObj list in the Target Region
        GateList = self.GateList
        gateNumber = len(self.GateList)
        connectMat = numpy.zeros(shape=(gateNumber, gateNumber))
        for gateObj in GateList:
            remainGateList = [Obj for Obj in GateList if Obj!=gateObj]
            idxGateObj = GateList.index(gateObj)
            for remainObj in remainGateList:
                NetListOfGateObj = gateObj.NetObjList
                NetListOfRemainObj = remainObj.NetObjList
                ConnectGateNet = list(set(NetListOfGateObj)&set(NetListOfRemainObj))
                if ConnectGateNet != []:
                    NetObj = ConnectGateNet[0]
                    idxRemainObj = GateList.index(remainObj)
                    #if idxGateObj==0 and idxRemainObj==3:
                    #    pdb.set_trace()
                    connectMat[idxGateObj][idxRemainObj] = NetObj.calWeight()
        self.connectMat = connectMat

    def buildAMatrix(self):
        A_Matrix = -1*self.connectMat
        GateInRegionList = self.GateList
        for GateObj in GateInRegionList:
            idxOfGate = GateInRegionList.index(GateObj)
            A_Matrix[idxOfGate][idxOfGate] = sum(abs(A_Matrix[idxOfGate]))
            NetOnGateList = GateObj.NetObjList
            for netObj in NetOnGateList:
                if netObj.PadList != []:
                    A_Matrix[idxOfGate][idxOfGate] = A_Matrix[idxOfGate][idxOfGate] + len(netObj.PadList)*netObj.calWeight()
                GateOnNetList = netObj.GateObjList
                GateNotInRegionList = list(set(GateOnNetList) - set(GateInRegionList))
                if GateNotInRegionList != []:
                     A_Matrix[idxOfGate][idxOfGate] = A_Matrix[idxOfGate][idxOfGate] + len(GateNotInRegionList)*netObj.calWeight()
        self.A_Matrix = A_Matrix
    def buildBVector(self, AssignmentFlag, boundaryNumber):
        GateInRegionList = self.GateList
        gateNumber = len(GateInRegionList)            
        self.b_x = numpy.array([0.0 for i in range(gateNumber)])
        self.b_y = numpy.array([0.0 for i in range(gateNumber)])
        for GateObj in GateInRegionList:
            idxOfGate = GateInRegionList.index(GateObj)
            NetOnGateList = GateObj.NetObjList
            for NetObj in NetOnGateList:
                PadObjList = NetObj.PadList
                #Calculate The PadList Weight On All the Net that connect to current Gate
                if PadObjList != []:
                    for PadObj in PadObjList:
                        #The QP1 Problem
                        if AssignmentFlag == "O":
                            self.b_x[idxOfGate] = self.b_x[idxOfGate] + PadObj.xCoord*NetObj.calWeight()
                            self.b_y[idxOfGate] = self.b_y[idxOfGate] + PadObj.yCoord*NetObj.calWeight()
                        elif AssignmentFlag == "L":
                            if PadObj.xCoord > boundaryNumber:
                                #print PadObj.padId, PadObj.xCoord
                                self.b_x[idxOfGate] = self.b_x[idxOfGate] + boundaryNumber*NetObj.calWeight()
                                self.b_y[idxOfGate] = self.b_y[idxOfGate] + PadObj.yCoord*NetObj.calWeight()
                            else:
                                self.b_x[idxOfGate] = self.b_x[idxOfGate] + PadObj.xCoord*NetObj.calWeight()
                                self.b_y[idxOfGate] = self.b_y[idxOfGate] + PadObj.yCoord*NetObj.calWeight()
                        elif AssignmentFlag == "R":
                            if PadObj.xCoord < boundaryNumber:
                                self.b_x[idxOfGate] = self.b_x[idxOfGate] + boundaryNumber*NetObj.calWeight()
                                self.b_y[idxOfGate] = self.b_y[idxOfGate] + PadObj.yCoord*NetObj.calWeight()
                            else:
                                self.b_x[idxOfGate] = self.b_x[idxOfGate] + PadObj.xCoord*NetObj.calWeight()
                                self.b_y[idxOfGate] = self.b_y[idxOfGate] + PadObj.yCoord*NetObj.calWeight()
                GateOnNetList = NetObj.GateObjList
                GateNotInRegionList = list(set(GateOnNetList) - set(GateInRegionList))
                #Calculate the gatePad weight
                if AssignmentFlag != "O" and GateNotInRegionList!=[]:
                    for GateObj in GateNotInRegionList:
                        self.b_x[idxOfGate] = self.b_x[idxOfGate] + boundaryNumber*NetObj.calWeight()
                        self.b_y[idxOfGate] = self.b_y[idxOfGate] + GateObj.yCoord*NetObj.calWeight()
                    
    def solveQP(self):
        self.X_VEC = numpy.linalg.solve(self.A_Matrix, self.b_x)
        self.Y_VEC = numpy.linalg.solve(self.A_Matrix, self.b_y)
        GateList = self.GateList
        i = 0
        for GateObj in GateList:
            GateObj.xCoord = self.X_VEC[i]
            GateObj.yCoord = self.Y_VEC[i]
            i = i + 1
    
        
def GenOutputFile(filePath, GateObjDict):
    outFile = open(filePath, "w")
    for gateId in GateObjDict:
        outFile.write(str(gateId)+" "+str(GateObjDict[gateId].xCoord)+" "+str(GateObjDict[gateId].yCoord)+"\n")
    outFile.close()

if __name__ == "__main__":
    NetToGateDict, NetToPadDict, gateNumber = buildNetToGateDict("D:/Users/chientut/Documents/Course/CAD_VLSI/HW/ProgrammingAssignment3Files/benchmarks/8x8 QP/biomed")
    #Solve The QP1Problem
    QPObj = Placement()
    QPObj.buildNetList(NetToGateDict, NetToPadDict)
    QPObj.buildGateList("O")
    QPObj.buildConnectMatrix()
    QPObj.buildAMatrix()
    QPObj.buildBVector("O", 50)
    QPObj.solveQP()
    #Solve The QP2 Problem
    QPObj.buildGateList("L")
    QPObj.buildConnectMatrix()
    QPObj.buildAMatrix()
    QPObj.buildBVector("L", 50)
    QPObj.solveQP()
    #Solve The QP3 Problem
    QPObj.buildGateList("R")
    QPObj.buildConnectMatrix()
    QPObj.buildAMatrix()
    QPObj.buildBVector("R", 50)
    QPObj.solveQP()
    GenOutputFile("D:/Users/chientut/Documents/Course/CAD_VLSI/HW/ProgrammingAssignment3Files/benchmarks/8x8 QP/testOut.txt", QPObj.GateObjDict)
    pdb.set_trace()















    







    
