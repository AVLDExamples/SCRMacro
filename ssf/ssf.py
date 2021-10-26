#!/usr/bin/env python
#!/usr/bin/env python
#
# v1.1.2
# SCRMacro for FIRE_WM v2017
# author: C. Schmalhorst
# (C) AVL Deutschland GmbH
# @date=20170322
# @version=112
#
# class FireCase courtesy of Mark Olesen, Faurecia Emission Control Technologies, Augsburg
#
#------------------------------------------------------------------------------
#
import math
import os
import re
import shlex
import subprocess
import sys
import act.units
import gtk
import StringIO
import xml.etree.ElementTree as ET

class SSFNode2:

    def __init__(self, line):
        tokens = line.split()
        self.name = tokens[2][1:-1]
        self.longname = tokens[1][1:-1]
        self.contents = [line]
        self.simplevalues = dict()

    def __getattr__(self, attr):
        if attr in self.__dict__.keys():
            return self.__dict__[attr]
        if attr in self.simplevalues.keys():
            return self.simplevalues[attr]
        raise AttributeError

    def addline(self, line):
        self.contents.append(line)
        tokens = line.split()  # much quicker than shlex.split()
        if '"no_unit~' in tokens:
            tokens.remove('"no_unit~')
            tokens.remove('"')
        if len(tokens) == 3:
            if tokens[1] == 'int':
#                 self.simplevalues[tokens[0]] = int(tokens[2])
                self.__dict__[tokens[0]] = int(tokens[2])
            elif tokens[1] == 'double':
#                 self.simplevalues[tokens[0]] = float(tokens[2])
                self.__dict__[tokens[0]] = float(tokens[2])
            elif tokens[1] == 'string':
#                 self.simplevalues[tokens[0]] = tokens[2][1:-1]  # strip "
                self.__dict__[tokens[0]] = tokens[2][1:-1]  # strip "

        elif len(tokens) > 3 and tokens[1] == 'string':
            # quoted string?
            tokens = shlex.split(line)
            if len(tokens) == 3:
#                 self.simplevalues[tokens[0]] = tokens[2]  # no stripping of " needed
                self.__dict__[tokens[0]] = tokens[2]  # no stripping of " needed
        elif len(tokens) == 4:
            if tokens[1] == 'double':
                try:
                    unit = act.units.find( tokens[3][1:-1] )
                    value = float(tokens[2])
#                     self.simplevalues[tokens[0]] = act.units.Amount(value,unit)
                    self.__dict__[tokens[0]] = act.units.Amount(value,unit)
                except act.units.UnitError:
                    pass
                except ValueError:
                    print tokens
            pass


    @staticmethod
    def readSSF(filename):
        try:
            print filename
            infile = open(filename, "r");
            contents = infile.readlines();
            infile.close()
            root = SSFNode2(contents[0])
            SSFNode2.__readNode(root, 1, contents)
            return root
        except IOError, ex:
            raise ex

    @staticmethod
    def __readNode(node, i, contents):
        while i < len(contents):
            line = contents[i]
            i += 1
            tokens = line.split()
            if len(tokens) > 0:
                if tokens[0] == '_C_':
                    newnode = SSFNode2(line)
                    node.contents.append(newnode)
                    if newnode.name in node.__dict__:
                        if type(node.__dict__[newnode.name]) is not list:
                            dummy = node.__dict__[newnode.name]
                            node.__dict__[newnode.name] = [dummy]
                        node.__dict__[newnode.name].append(newnode)
                    else:
                        node.__dict__[newnode.name] = newnode
                    i = SSFNode2.__readNode(newnode, i, contents)
                elif tokens[0] == '..':
                    return i
                else:
                    node.addline(line.strip())
        return i



class SSFNode(dict):

    def __init__(self, line):
        tokens = line.split()
        self.name = tokens[2][1:-1]
        self.longname = tokens[1][1:-1]
        self.contents = [line]
        self.simplevalues = dict()

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]
        if attr in self.simplevalues.keys():
            return self.simplevalues[attr]
        raise AttributeError

    def addline(self, line):
        self.contents.append(line)
        tokens = line.split()  # much quicker than shlex.split()
        if '"no_unit~' in tokens:
            tokens.remove('"no_unit~')
            tokens.remove('"')
        if len(tokens) == 3:
            if tokens[1] == 'int':
                self.simplevalues[tokens[0]] = int(tokens[2])
            elif tokens[1] == 'double':
                self.simplevalues[tokens[0]] = float(tokens[2])
            elif tokens[1] == 'string':
                self.simplevalues[tokens[0]] = tokens[2][1:-1]  # strip "

        elif len(tokens) > 3 and tokens[1] == 'string':
            # quoted string?
            tokens = shlex.split(line)
            if len(tokens) == 3:
                self.simplevalues[tokens[0]] = tokens[2]  # no stripping of " needed
        elif len(tokens) == 4:
            if tokens[1] == 'double':
                try:
                    unit = act.units.find( tokens[3][1:-1] )
                    value = float(tokens[2])
                    self.simplevalues[tokens[0]] = act.units.Amount(value,unit)
                except act.units.UnitError:
                    pass
                except ValueError:
                    print tokens
            pass


    @staticmethod
    def readSSF(filename):
        try:
            print filename
            infile = open(filename, "r");
            contents = infile.readlines();
            infile.close()
            root = SSFNode(contents[0])
            SSFNode.__readNode(root, 1, contents)
            return root
        except IOError, ex:
            raise ex

    @staticmethod
    def __readNode(node, i, contents):
        while i < len(contents):
            line = contents[i]
            i += 1
            tokens = line.split()
            if len(tokens) > 0:
                if tokens[0] == '_C_':
                    newnode = SSFNode(line)
                    node.contents.append(newnode)
                    if newnode.name in node:
                        name_search = True
                        k=1
                        while name_search:
                            if newnode.name+str(k) not in node:
                                name_search = False
                                newnode.name =  newnode.name+str(k)
                            k = k+1
                    node[newnode.name] = newnode
                    i = SSFNode.__readNode(newnode, i, contents)
                elif tokens[0] == '..':
                    return i
                else:
                    node.addline(line.strip())
        return i

def correctSSF_2D_Results_Names(filename):
    try:
        infile = open(filename, "r")
        contents = infile.readlines()
        infile.close()
        for i in range(len(contents)):
            if contents[i].find("OutputControl2D_OutputSelectionData") != -1 and contents[i].find("NoName") != -1 :
                # needs correction!
                # peek ahead
                j = i + 1
                while contents[j].find("Name") == -1:
                    j = j + 1
                toks = contents[j].split()
                newName = toks[2][1:-1]
                i_start = contents[i].find("NoName")
                i_end = i_start + len("NoName")
                contents[i] = contents[i][0:i_start] + newName + contents[i][i_end:]

        return contents
    except IOError, ex:
        raise ex


def getVersion():
    configFilePath = os.path.join( os.getenv("AVLAST_HOME"), "config", "product.xml" )
    if os.path.exists( configFilePath ):
        xmlfile = ET.parse(configFilePath)
        xmlroot = xmlfile.getroot()
        configels = xmlroot.findall('config')
        for product in configels:
            el = product.find('product')
            if el.get('name')=='FIRE Classic':
                version = el.get('version')
                return version
    for line in sys.path:
        parts = line.split(os.path.sep)
        if 'CFDWM' in parts:
            i = parts.index('CFDWM')
            version = parts[i+1]
            if not version.startswith('v'):
                version = 'v2017'
            return version
    return ''
#------------------------------------------------------------------------------
#
#
class FireCase:
    @staticmethod
    def getCaseList(projectDir):
        """
        look through the Calculation/ directory for possible cases
        return as sorted list
        """
        cases = []
        # print "proj =", projectDir

        if projectDir != None:
            calcDir = os.path.join(projectDir, 'Calculation')
            # print "calc =", projectDir

            if os.path.isdir(calcDir):
                for name in sorted(os.listdir(calcDir)):
                    if os.path.exists(os.path.join(calcDir, name, name + ".ssf")):
                        cases.append(name)

        return cases


    @staticmethod
    def getCaseCombo(projectDir, default=None):
        """
        look through the Calculation/ directory for possible cases
        return sorted list as a GTK combo box. Optionally preselect specified case
        """
        names = FireCase.getCaseList(projectDir);

        combo = gtk.combo_box_new_text()
        for i in range(len(names)):
            combo.append_text(names[i])
            if names[i] == default:
                combo.set_active(i)

        return combo


    def __init__(self, projectDir=None, caseName=None, verbose=False):
        try:
            defDir = PM_GetProjectIOData()[1]  # project directory (absolute path)
            fireOk = True
        except NameError:
            defDir = os.getcwd()
            fireOk = False

        self.verbose  = verbose
        self.hasFire  = fireOk
        self.error    = None

        self.projDir  = defDir if projectDir == None else projectDir
        print defDir, self.projDir
        self.calcDir  = os.path.join(self.projDir, 'Calculation')
        self.caseDir  = None
        self.caseName = None
        self.ssfName  = None
        self.ssfFile  = None

        self.setCase(caseName)
        return


    def setCase(self, caseName):
        """
        Set the case name (should exist in Calculation/ directory)
        """
        # clear old values
        self.caseDir  = None
        self.caseName = None
        self.ssfName  = None
        self.ssfFile  = None
        self.error    = None

        if caseName == None:
            return False

        caseName = re.sub(r'\.ssf$', '', caseName)    ## without .ssf extension
        caseName = re.sub(r'/+$', '', caseName)       ## no trailing slash
        caseName = re.sub(r'^.*/', '', caseName)      ## strip leading directory names

        caseDir = os.path.join(self.calcDir, caseName)
        ssfName = caseName + '.ssf'
        ssfFile = os.path.join(caseDir, ssfName)
        if not os.path.isdir(caseDir):
            self.error = "invalid case directory '" + caseName + "' in " + self.projDir
            if self.verbose == True:
                print self.error
            return

        if not os.path.isfile(ssfFile):
            self.error = "invalid case - no '" + ssfName + "' in " + self.projDir
            if self.verbose == True:
                print self.error
            return

        self.caseDir  = caseDir
        self.caseName = caseName
        self.ssfName  = ssfName
        self.ssfFile  = ssfFile

        if self.verbose == True:
            print "ssfFile:", self.ssfFile

        return self.caseName != None

    def mkdir(self, directory):
        """
        concatenate dir to the project-directory, creating it as required
        """
        outdir = os.path.join(self.projDir, directory)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        return outdir


    def hasError(self):
        """
        True if any error was recorded during setCase
        """
        return self.error != None


    def hasCalcDir(self):
        """
        True if the project directory has a Calculation/ directory
        """
        return os.path.isdir(self.calcDir)


    def hasCaseDir(self):
        """
        True if the project directory has a Calculation/CASE/ directory
        """
        return self.caseDir != None and os.path.isdir(self.caseDir)


    def isValidProjectDir(self, verbose=None):
        """
        True if the project directory appears valid
        - require .fpr file and Calculation/ directory
        """
        okay = os.path.isdir(self.projDir) and os.path.isdir(self.calcDir)

        if okay:
            okay = False
            for name in os.listdir(self.projDir):
                if name.endswith('.fpr'):
                    okay = True
                    break

        if verbose == True or verbose == None and self.verbose == True:
            print "project dir:", os.path.abspath(self.projDir)

        return okay

    def applySSC(self, sscFilename):
        commando = []
        wm_version = getVersion()
        wm_home = os.getenv('AVLAST_HOME')
        #commando.append( os.path.join( wm_home,'bin','fire_wm'))

        print wm_version

        if os.name == 'posix':
            commando.append( os.path.join( wm_home,'bin','fire_wm_merge_ssc' ) )
        else:
            commando.append( os.path.join( wm_home,'bin','fire_wm_merge_ssc.exe' ) )
        commando.append('-ssf')
        commando.append( os.path.abspath( self.ssfFile ))
        commando.append("-cfg" )
        commando.append(os.path.abspath( sscFilename ))

        print commando
        subprocess.call(commando)
