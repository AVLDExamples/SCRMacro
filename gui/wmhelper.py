#!/usr/bin/env python
#
# v1.1.2
# SCRMacro for FIRE_WM v2017
# author: C. Schmalhorst
# (C) AVL Deutschland GmbH
# @date=20170322
# @version=112
#
from _guipm import FC_GuiPMGetMeshesUnderCase
from _pre import PreFameToolsGetCellSelectionsFromFlmFile, PreFameToolsGetFaceSelectionsFromFlmFile, PreGeoInfoGetNumSurfaceFaces
from _projectmanager import PM_GetMeshFileName
import json
import act
from pkg_resources import resource_stream

class SelColumn(act.Base):
    act.namespace.defclass
    defslot( "Selection", type=str)
    defslot( "Evaporation", type = bool, initval = False)
    defslot( "UI", type = bool, initval = False)
    defslot( "Wallfilm", type = bool, initval = False)
    defslot( "SelType", type = str, initval = 'Cell')


def populateListForCasename(case):
    """For the given case, the selections of the first mesh are loaded, cell selections and face selections separately.
    Selections names are sorted according to the naming convention saved in the file naming_convention.json
    returns a list of lists:
               EVAP  UI    WALLFILM
    [
        [ str, bool, bool, bool, "Cell"|"Face"],
    ]
    """
    selections=[]
    mesh = FC_GuiPMGetMeshesUnderCase(case,0,0)[0]
    cellSelnames = PreFameToolsGetCellSelectionsFromFlmFile(PM_GetMeshFileName(mesh))
    faceSelnames = PreFameToolsGetFaceSelectionsFromFlmFile(PM_GetMeshFileName(mesh))

    naming_convention = json.load(resource_stream('gui', 'naming_convention.json'))

    cellSelnames.sort()
    faceSelnames.sort()

    for sel in cellSelnames:
        line = SelColumn()
        line.Selection = sel
#        line = [sel, False, False, False, 'Cell']
        selections.append(line)

        for name in naming_convention['EVAP']:
            if name in sel.lower():
                line.Evaporation = True
                break
        for name in naming_convention['UI']:
            if name in sel.lower():
                line.UI = True
                break

    for sel in faceSelnames:
        line = SelColumn()
        line.Selection = sel
        line.SelType = 'Face'
#        line = [sel, False, False, False, 'Face']
        selections.append(line)
        for name in naming_convention['WALLFILM']:
            if name in sel.lower():
                line.Wallfilm = True
                break
        for name in naming_convention['UI']:
            if name in sel.lower():
                line.UI = True
                break

    return selections
