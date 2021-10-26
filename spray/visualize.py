#!/usr/bin/env python
#
# v1.1.2
# SCRMacro for FIRE_WM v2017
# author: C. Schmalhorst
# (C) AVL Deutschland GmbH
# @date=20170322
# @version=112
#
import numpy as np
import math
import os

from _cfdwm import *
from _pre import *
from _fameenginetng import *
from _guibar2dmacro import *
from _guigraph import *
from _guiimpress import *
from _guimeshchecks import *
from _guipm import *
from _guisolver import *
from _oglviewer import *
from _post import *
from _projectmanager import *

display_axis = 1            # type 1 to display spray axis in GUI
display_cones = 1            # type 1 to display spray cone in GUI
multiplier = 0.1            # all vectors will be scaled to this length value (m)
resolution = 40


#----------------------------------------------------------
NonSILength = {'m':1,'dm':0.10,'cm':0.01,'mm':0.001,'microns':1e-6,'yd':0.914,'ft':0.304804,'in':0.0254, 'mym':1e-6}
NonSIAngle  = {'deg': math.pi/180. ,'rad':1}
UNITS = { 'length':NonSILength,    'angle':NonSIAngle}
#-----------------------------------------------------------

def readValueFromSSF(myvalue):
    groesse = myvalue[3][1:-1].split('~')
    if(myvalue[1] == "double"):
        if len(groesse) == 1:
            return float(myvalue[2])
        else:
            return float(myvalue[2]) * UNITS[groesse[0]][groesse[1]]
    elif myvalue[1] == "int":
        return int(myvalue[2])
    else:
        return myvalue[2]

def makeVector( list1, list2, list3):
    """
        takes three lists of floats that must be of equal length (x, y, z)
        and creates a numpy array of 3 coords.
    """
    veclist = []
    for i in range(0,len(list1)):
        vec = np.zeros(3)
        vec[0] = list1[i]
        vec[1] = list2[i]
        vec[2] = list3[i]
        veclist.append(vec)
    return veclist

def getKsi(rotvec):
    """
        Creates the KSI axis as used in FIRE local spray coordinate system
    """
    ksi = np.cross(rotvec,(0,0,1))
    xy = False
    if (np.linalg.norm(ksi)<1e-30):
        xy = True
        ksi = np.cross(rotvec,(0,1,0))

    ksi /= np.linalg.norm(ksi)
    if xy:
        if ksi[0]<0:
            ksi=-ksi
    else:
        if ksi[1]<0:
            ksi = -ksi
    return ksi

def makeAxisRotation(direction, angle):
    """
        Creates a numpy array for the rotation about axis direction with angle
    """
    d = np.array(direction)
    d/=np.linalg.norm(d)
    eye = np.eye(3)
    ddt = np.outer(d,d)
    skew = np.array( [ [0, -d[2], d[1]],
                     [d[2], 0, -d[0]],
                     [-d[1], d[0],0] ])
    mtx = ddt + np.cos(angle) * (eye-ddt) + np.sin(angle)*skew
    return mtx

def makeCone(direction, ksi, length, resolution, d1, angle, reverse=False):
    """
        returns an array of points which approximates an open cone
    """
    print d1, angle
    retval = []
    if reverse:
        rot = makeAxisRotation(direction, math.pi*2./resolution)
    else:
        rot = makeAxisRotation(direction, -math.pi*2./resolution)

    for i in range(0, resolution):
        p1 = ksi*d1
        p2 = direction*length + ksi*(d1+length*math.tan(angle))

        for i in range(0,len(retval)):
            retval[i] = np.dot(rot, retval[i])

        retval.append(p1)
        retval.append(p2)

    return retval

def writeConeAsFLMA(cones, filename):
    """
        cones is a list of lists of points
        cones List<List<ndarray>>
        writes cones coded in points into filename in .flma-format
    """
    totnump = 0
    for cone in cones:
        totnump += len(cone)

    if not filename.endswith(".flma"):
        filename += ".flma"

    coneflma = open(filename, "w")
    coneflma.write(str(totnump))
    coneflma.write("\n")
    for points in cones:
        for p in points:
            coneflma.write( " %g %g %g" % (p[0], p[1], p[2]) )
        coneflma.write("\n")
    coneflma.write(" %d\n" % (totnump/2))
    totnump = 0
    for points in cones:
        np = len(points)
        i =0
        while i<np:
            coneflma.write("4\n %d %d %d %d\n" %(
                (i%np)+totnump,
                ((i+1)% np)+totnump,
                ((i+3) % np)+totnump,
                ((i+2) %np)+totnump))
            i += 2
        coneflma.write("\n")
        totnump += np
    coneflma.write(" %d\n" % (totnump/2))
    for i in range(0, totnump/2):
        coneflma.write(" 3")
    coneflma.write("\n\n0\n")
    coneflma.close()

def make_spraycones(firecase):

    #print dir()

    if hasattr(firecase, 'ssfFile'):


        ssfpath=firecase.ssfFile
    else:
        ssfpath = firecase

    with open(ssfpath, "r") as ssf:
        j = 1
        ssftxt = ssf.read()
        n = ssftxt.count('ge01')
        nozzles = n-1
#        print "found ", nozzles, "nozzles"
        ssf.close()

#    logFilePath=os.path.join(macropath,'sprayCones.log')
#    log=open(logFilePath,'w')
#    log.close()
#    log=open(logFilePath,'a')

    tokenSearch = {
            'ge01':[],    # nozzle x-coordinates
            'ge02':[],    # nozzle y-coordinates
            'ge03':[],    # nozzle z-coordinates
            'ge04':[],    # nozzle x-direction
            'ge05':[],    # nozzle y-direction
            'ge06':[],    # nozzle z-direction
            'ge11':[],    # diameter at hole center position
            'ge12':[],    # number of nozzle holes
            'ge13':[],    # delta 1: orientation angle
            'ge14':[],    # delta 2: rotation angle
            'ge15':[],    # circumferential distribution
            'di05':[],    # half outer cone angle
            'di06':[],    # half inner cone angle
            'di03':[],    # outer diameter
            'di04':[]    # inner diameter
    }

    with open(ssfpath, "r") as ssf:
        # loop counts number of nozzles and gets necessary data
        for line in ssf.readlines():
                tokens = line.split()
                if len(tokens)>0:
                        if tokens[0] in tokenSearch.keys():
                            tokenSearch[tokens[0]].append(readValueFromSSF(tokens))


    ge11_list = tokenSearch['ge11']
    ge12_list = tokenSearch['ge12']
    ge13_list = tokenSearch['ge13']
    ge14_list = tokenSearch['ge14']
    ge15_list = tokenSearch['ge15']
    di05_list = tokenSearch['di05']
    di06_list = tokenSearch['di06']
    di03_list = tokenSearch['di03']
    di04_list = tokenSearch['di04']

    inozzles = int(nozzles)


    #prepare array for finding identical nozzles (timing might be different)
    NOZ=[[] for i in range(inozzles)]
    print inozzles
    for l in range(0,inozzles):
            NOZ[l].append(tokenSearch['ge01'][l])
            NOZ[l].append(tokenSearch['ge02'][l])
            NOZ[l].append(tokenSearch['ge03'][l])
            NOZ[l].append(tokenSearch['ge04'][l])
            NOZ[l].append(tokenSearch['ge05'][l])
            NOZ[l].append(tokenSearch['ge06'][l])
            NOZ[l].append(tokenSearch['ge11'][l])
            NOZ[l].append(tokenSearch['ge12'][l])
            NOZ[l].append(tokenSearch['ge13'][l])
            NOZ[l].append(tokenSearch['ge14'][l])
            NOZ[l].append(tokenSearch['ge15'][l])
            NOZ[l].append(tokenSearch['di05'][l])
            NOZ[l].append(tokenSearch['di06'][l])
            NOZ[l].append(tokenSearch['di03'][l])
            NOZ[l].append(tokenSearch['di04'][l])

    g=0
    for nozz in NOZ:
            print nozz
            if NOZ.count(nozz)>1:
                    NOZ[g]=[]
                    #NOZ.remove(nozz)
            g=g+1

    # now identical nozzles are marked, as they do not appear in list NOZ
    # create location and direction vectors. Normalize direction vectors
    locvecs = makeVector(tokenSearch['ge01'], tokenSearch['ge02'], tokenSearch['ge03'])
    dirvecs = makeVector(tokenSearch['ge04'], tokenSearch['ge05'], tokenSearch['ge06'])
    for i in range(0,len(dirvecs)):
        p =dirvecs[i]
        if np.linalg.norm(p)>1e-20:
            dirvecs[i] = p/np.linalg.norm(p)
        else:
            print ' problem for nozzle, vector ',i,' is null:', dirvecs[i]
            return

    for k in range(0, len(NOZ)):
        if NOZ[k]==[]:
            pass
        else:
            print "nozzle", k+1
            print "   "
    # get nozzle values

            hd = ge11_list[k]
            nh = ge12_list[k]            # number of nozzle holes
            print "nh = " + str(nh)
            delta_1_rad = ge13_list[k]            # angle  delta1 (Spreizwinkel)
            delta_2_rad = ge14_list[k]            # angle delta2 (verdrehung der Duese)
            di = ge15_list[k]            # distribution

            outercone = di05_list[k]            # outer cone angle
            innercone = di06_list[k]            # inner cone angle
            outerdiam = di03_list[k]            # outer diameter
            innerdiam = di04_list[k]            # innerdiam

            rotvec = dirvecs[k]
            locvec = locvecs[k]
            sprayvec = -rotvec

    # calculate nozzle ksi-axis by cross product
    # ksi is on x-y-plane, i.e. plane normal = (0, 0, 1)
    # exception: nozzle direction = (0, 0, 1), then ksi is the x-axis
            print rotvec
            ksi = getKsi(rotvec)
            eta = np.cross(ksi, rotvec)
    # get normalized ksi-axis
            print "ksi-axis"
            print str(ksi)
            print "eta-axis"
            print str(eta)
            rot1 = makeAxisRotation(eta, delta_1_rad/2.)
            print str(rot1)
            rot2 = makeAxisRotation(rotvec, delta_2_rad) # incremental rotation of full nozzle
            if di==0:
                rot_angle = math.pi*2./nh
            else:
                print "di:", di
                rot_angle = di/180.*math.pi  # sic!
            rot3 = makeAxisRotation(rotvec, rot_angle)
            sprayvex = []
            inconevex = []
            outconevex = []

            for i in range(0,nh):
                if outerdiam > 0:
                    outcone = makeCone(sprayvec, ksi, multiplier, resolution, outerdiam/2, outercone)
                    for i in range(0,len(outcone)):
                        p = outcone[i]
                        p = np.dot(rot1, p)
                        np.add(p,ksi*hd/2,p)
                        p = np.dot(rot2, p)
                        outcone[i] = p
                else:
                    outcone = None

                if innercone > 0:
                    incone = makeCone(sprayvec, ksi, multiplier, resolution, innerdiam/2, innercone,True)
                    for i in range(0,len(incone)):
                        p = incone[i]
                        p = np.dot(rot1, p)
                        np.add(p,ksi*hd/2,p)
                        p = np.dot(rot2, p)
                        incone[i] = p
                else:
                    incone = None

                p1 = np.zeros(3)
                p2 = sprayvec*multiplier
                p1 = np.dot(rot1, p1)
                p2 = np.dot(rot1, p2)
                np.add(p1, ksi*hd/2, p1)
                np.add(p2, ksi*hd/2, p2)
                p1 = np.dot(rot2, p1)
                p2 = np.dot(rot2, p2)

                for j in range(0,len(sprayvex)):
                    sprayvex[j] = np.dot(rot3, sprayvex[j])

                for cone in inconevex:
                    if not cone ==None:
                        for j in range(0,len(cone)):
                            cone[j] = np.dot(rot3,cone[j])
                for cone in outconevex:
                    if not cone ==None:
                        for j in range(0,len(cone)):
                            cone[j] = np.dot(rot3,cone[j])

                sprayvex.append(p1)
                sprayvex.append(p2)
                outconevex.append(outcone)
                if incone:
                    outconevex.append(incone)

            for p in sprayvex:
                p += locvec

            for cone in outconevex:
                if not cone ==None:
                    for p in cone:
                        p +=locvec

            if display_cones:
                outconename = "cone_noz_"+str(k)
                meshList = PreGetMeshes()
                for name in meshList:
                    if name.startswith(outconename):
                        ViewerDelete(GuiGetActiveViewerName(), name)
                outconeoutname = os.path.join(firecase.caseDir, outconename+ ".flma")
                writeConeAsFLMA(outconevex, outconeoutname)
                PreLoadNative(str(outconename) + "(1)", outconeoutname );
                #GuiUpdate(0,0)

            if display_axis:
                flmaname = "spray-axis_noz_" + str(k)
                meshList = PreGetMeshes()
                for name in meshList:
                    if name.startswith(flmaname):
                        ViewerDelete(GuiGetActiveViewerName(), name)
                flmaoutname = flmaname +".flma"
                with open(os.path.join(firecase.caseDir,flmaoutname), "w") as flmaout:
                    flmaout.write(str(len(sprayvex)))
                    flmaout.write("\n")
                    for i in range(0,len(sprayvex)):
                        flmaout.write(" %g %g %g" % ( sprayvex[i][0],sprayvex[i][1],sprayvex[i][2]  ))
                    flmaout.write("\n%d\n" % (len(sprayvex)/2))
                    for i in range(0, len(sprayvex),2):
                        flmaout.write( "2\n%d %d\n" % ( i, i+1 ))

                    flmaout.write("\n%d\n" % (len(sprayvex)/2))
                    for i in range(0, len(sprayvex),2):
                        flmaout.write( " 1")
                    flmaout.write("\n\n0\n" )

                PreLoadNative(str(flmaname) + "(1)", str(os.path.join(firecase.caseDir,flmaoutname)) );
