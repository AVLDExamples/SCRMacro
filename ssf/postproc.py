#!/usr/bin/env python
#
# v1.1.2
# SCRMacro for FIRE_WM v2017
# author: C. Schmalhorst
# (C) AVL Deutschland GmbH
# @date=20170322
# @version=112
#

import StringIO
import os
import shutil
from string import Template
from pkg_resources import resource_listdir, resource_stream, resource_filename
import act.units
import spray
import ssf
import json

DEGREE = act.units.find('angle~deg')


def toDegree(amount):
    return amount.am_in(DEGREE).value


#---------------------------------------------------------------------------------------------
#SSC Snippets
#---------------------------------------------------------------------------------------------
# string.format() inputs :
# {numGlFormula}
# {GlobalFormula}
SSCFileFrml = r"""
###setting formula for variable "Solver->Global formula definitions->Formula_1_formula"
set-const solver.GFD.numGlFormulas {numGlFormula}
#v2017# add solver.GFD.Formula_{numGlFormula}_formula MyFormula
set-formula solver.GFD.Formula_{numGlFormula}_formula "{GlobalFormula}"
"""


# String inputs : (not a template!!!)
# {TotNumFormula}
SSCFileResult_Header = r"""
###setting value for variable "Solver->Output control->Write 3D result file->@numFormulasIn3DRes"
set-const solver.OC.W3DRF.numFormulasIn3DRes {TotNumFormula}
"""

# String inputs : (not a template!!!)
# {NumFormula}
# {ResultFormula}
# {FormulaName}
SSCFileResult = r"""
###adding to class list "Solver->Output control->Write 3D result file->Formula_1_formula"
#v2017#  add solver.OC.W3DRF.Formula_{NumFormula}_formula FormulaQuantity
###setting value for variable "Solver->Output control->Write 3D result file->Formula_1_formula->Formel"
set-const solver.OC.W3DRF.Formula_{NumFormula}_formula.Name "{FormulaName}"
###setting formula for variable "Solver->Output control->Write 3D result file->Formula_1_formula"
set-formula solver.OC.W3DRF.Formula_{NumFormula}_formula "{ResultFormula}"



"""
#template inputs:
#${NumSelectionsFor2DResults}
#this template can be included once!
SSCFile2DResult_Header = r"""
###adding to class list "Solver->Output control->Write 2D result file->2D[${NumSelectionsFor2DResults}]"
add solver.OC.W2DOUTPUT.NoName[${NumSelectionsFor2DResults}]
"""
#template inputs:
#${SelectionIndex}
#${NumFormulas}
#${SelectionName}
SSCFile2DResult = r"""
###setting value for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Name of 2D output"
set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].Name "${SelectionName}"
###setting value for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Sel. for 2D output"
set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].Selection "${SelectionName}"
###setting value for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Flow quantities"
set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].flowQuant 1
###setting value for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Turbulence quantities"
set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].turQuant 1
###setting value for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Mass flow"
set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].massFlow 1
###setting value for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->@numFormulasIn2DRes"
set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].numFormulasIn2DRes ${NumFormulas}
###setting value for variable "Solver->Output control->Write 2D result file->${SelectionName}[${SelectionIndex}]->@tree_title"
#set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].tree_title "${SelectionName}"



"""
#template inputs:
#${SelectionIndex}
#${Frml2DResultsIndex}
SSCFile2DResult_Formula = r"""
###adding to class list "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Formula_${Frml2DResultsIndex}_formula"
add solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].Formula_${Frml2DResultsIndex}_formula FormulaQuantity


"""


SSCSpeciesResult = r"""
###Species mole fractions
set-const solver.MO.ST.ST3D.spmolfr 1


"""
#Inputs
# {0} : number of 2D Result
# {1} : name of cell selection
SSCSpecies2DResult = r"""
###adding to class list "Solver->Modules->Species transport->2D results->2D[{0}]"
add solver.MO.ST.ST2D.NoName[{0}]
###setting value for variable "Solver->Modules->Species transport->2D results->2D[{0}]->@visST"
set-const solver.MO.ST.ST2D.NoName[{0}].visST 1
###Sel. for 2D output
set-const solver.MO.ST.ST2D.NoName[{0}].Selection "{1}"
###Name of 2D output
set-const solver.MO.ST.ST2D.NoName[{0}].Name "{1}"
###Mean species mass fluxes face averaged
set-const solver.MO.ST.ST2D.NoName[{0}].meanspmassflux 1
###Mean accumulated species mass fluxes face averaged
set-const solver.MO.ST.ST2D.NoName[{0}].meanaccspmassflux 1
###Mean species mole fluxes face averaged
set-const solver.MO.ST.ST2D.NoName[{0}].meanspmoleflux 1
###Mean accumulated species mole fluxes face averaged
set-const solver.MO.ST.ST2D.NoName[{0}].meanaccspmoleflux 1



"""

#Inputs
# {0} : number of 2D Result
# {1} : name of cell selection
SSCSpray2DResult = r"""
#####################################################################################################################
#####################################################################################################################
###2D Results for Spray #############################################################################################
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################
###adding to class list "Solver->Modules->Spray->General settings for all particles->2D results->2D[{0}]"
add solver.MO.SP.GEN.output1.NoName[{0}]

###Sel. for 2D output
set-const solver.MO.SP.GEN.output1.NoName[{0}].Selection "{1}"
###Name of 2D output
set-const solver.MO.SP.GEN.output1.NoName[{0}].Name "{1}"
###Total liquid mass remaining
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou05 1
###Total liquid mass impinged
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou06 1
###Total liquid mass deserted
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou07 1
###d10-arithmetic mean diameter
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou9 1
###d30-volume mean diameter
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou10 1
###DV10
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou15 1
###DV50
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou16 1
###DV90
set-const solver.MO.SP.GEN.output1.NoName[{0}].ou17 1


"""
#template inputs:
#${SelectionIndex}
#${Frml2DResultsIndex}
#${PathToFrml}
#${FrmlName}
SSCFile2DResult_Formula_Body = r"""
###setting value for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Formula_${Frml2DResultsIndex}_formula->Formel"
set-const solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].Formula_${Frml2DResultsIndex}_formula.Name ${FrmlName}
###setting formula for variable "Solver->Output control->Write 2D result file->2D[${SelectionIndex}]->Formula_${Frml2DResultsIndex}_formula"
set-formula solver.OC.W2DOUTPUT.NoName[${SelectionIndex}].Formula_${Frml2DResultsIndex}_formula ${PathToFrml}
"""
#Timestep snippet, inputs
# {0}: endtime
# {1}: path to timestep.gid
# {2}: Path to 3D result output frequency
# {3}: path to backup output frequency
SSCTimestepInfo = r"""
###setting value for variable "Solver->Solver control->Convergence criteria->Max. number of iterations"
set-const solver.SC.CD.MinNumberIteration 3
set-const solver.SC.CD.MaxNumberIteration 45

###setting value for variable "Solver->Run mode->Run mode"
set-const solver.RM.Timesteps "Timestep"
###setting unit for variable "Solver->Run mode->Delta_t"
set-unit solver.RM.DeltaT time,s
###setting table for variable "Solver->Run mode->Delta_t"
set-table solver.RM.DeltaT {1}
###setting table unit for variable "Solver->Run mode->DeltaT_table"
set-table-unit solver.RM.DeltaT_table 1 time,s
###setting table unit for variable "Solver->Run mode->DeltaT_table"
set-table-unit solver.RM.DeltaT_table 2 time,s
###setting value for variable "Solver->Run mode->End time"
set-const solver.RM.endTime {0}
set-unit solver.RM.endTime time,s
###setting value for variable "Solver->Output control->Write backup file->Write backup file"
set-const solver.OC.WBF.bBackupFile 1
###setting unit for variable "Solver->Output control->Write backup file->Output frequency"
set-table solver.OC.WBF.each {3}
set-table-unit solver.OC.WBF.each_table 1 time,s
set-table-unit solver.OC.WBF.each_table 2 time,s
###setting value for variable "Solver->Output control->Write restart file->Write restart file"
set-const solver.OC.WRF.bRestartFile 0

###setting unit for variable "Solver->Output control->Write 3D result file->Output frequency"
set-unit solver.OC.W3DRF.each time,s
###setting table for variable "Solver->Output control->Write 3D result file->Output frequency"
set-table solver.OC.W3DRF.each {2}
###setting table unit for variable "Solver->Output control->Write 3D result file->each_table"
set-table-unit solver.OC.W3DRF.each_table 1 time,s
###setting table unit for variable "Solver->Output control->Write 3D result file->each_table"
set-table-unit solver.OC.W3DRF.each_table 2 time,s
"""

#Spray and Wallfilm settings, inputs:
# {0}: Path to AdBlue mass fractions
SSCSprayGlobals = r"""
###setting value for variable "Solver->Module activation->Spray"
set-const solver.MA.actSpray 1

#------------------------------Spray type
# following for "Solver->Modules->Spray->Liquid properties->Property set->Set_1->"
# Number of fluids
set-const solver.MO.SP.LP.PS.Set_1.fluidtypesnr 3
# Set temperature
set-const solver.MO.SP.LP.PS.Set_1.fluidtemp 338.000000
# Set_1
set-table solver.MO.SP.LP.PS.Set_1 {0}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Activate particle introduction from nozzle"
set-const solver.MO.SP.IN.NO.activate 1
###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->NSIZES"
set-const solver.MO.SP.IN.NO.n_sizes 24
###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->NINTRO"
set-const solver.MO.SP.IN.NO.n_intro 2
###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->NCIRCD"
set-const solver.MO.SP.IN.NO.n_circd 2

# following for  "Solver->Modules->Spray->General settings for all particles->Spray globals->..."
# Solve U-velocity
set-const solver.MO.SP.GEN.solver.so01 1
# Solve V-velocity
set-const solver.MO.SP.GEN.solver.so02 1
# Solve W-velocity
set-const solver.MO.SP.GEN.solver.so03 1
# Solve mass
set-const solver.MO.SP.GEN.solver.so04 1
# Solve heat
set-const solver.MO.SP.GEN.solver.so05 1
# Virtual mass force
set-const solver.MO.SP.GEN.solver.virt_mass_force 0
# Pressure gradient
set-const solver.MO.SP.GEN.solver.press_grad 0
# Extended output
set-const solver.MO.SP.GEN.solver.sprextou 0
# U-momentum
set-const solver.MO.SP.GEN.solver.co01 1
# V-momentum
set-const solver.MO.SP.GEN.solver.co02 1
# W-momentum
set-const solver.MO.SP.GEN.solver.co03 1
# Mass
set-const solver.MO.SP.GEN.solver.co04 1
# Heat
set-const solver.MO.SP.GEN.solver.co05 1
# Tke
set-const solver.MO.SP.GEN.solver.co06 0
# Dissipation
set-const solver.MO.SP.GEN.solver.co07 0
# Void-fraction
set-const solver.MO.SP.GEN.solver.voidFract 0
# Output frequency
set-unit solver.MO.SP.GEN.globals.each time,s
# Momentum sources
set-const solver.MO.SP.GEN.solver.momsournew "Semi-implicit"
## Cluster parcels at surface of region without spray
set-const solver.MO.SP.GEN.solver.clust_por 1
# Cluster parcels at selection named as *_clustering
set-const solver.MO.SP.GEN.solver.clust_sel 1
# Use surface instead volume weighting for mean diameter
set-const solver.MO.SP.GEN.solver.clust_ave 1

#----------------------------------------Spray submodels

# following for "Solver->Modules->Spray->General settings for all particles->Submodels->..."
# Turbulent dispersion model
set-const solver.MO.SP.GEN.submodels.TurbDispersion "Disable"
# Activate enhanced evaporation and thermolysis at catalyst
set-const solver.MO.SP.GEN.submodels.actEnhEvapTherm 1
# Submodels->E7
set-const solver.MO.SP.GEN.submodels.su01_06_7 10.000000
# Submodels->E8
set-const solver.MO.SP.GEN.submodels.su01_06_8 10.000000

# Evaporation model
set-const solver.MO.SP.GEN.submodels.evapmodel "SCR-thermolysis"
# E1
set-const solver.MO.SP.GEN.submodels.su01_01_1 1.0
# E2
set-const solver.MO.SP.GEN.submodels.su01_01_2 1.0
###setting value for variable "Solver->Modules->Spray->General settings for all particles->Submodels->E1"
set-const solver.MO.SP.GEN.submodels.su01_06_1 1.0
###setting value for variable "Solver->Modules->Spray->General settings for all particles->Submodels->E2"
set-const solver.MO.SP.GEN.submodels.su01_06_2 1.0
###setting value for variable "Solver->Modules->Spray->General settings for all particles->Submodels->E3"
set-const solver.MO.SP.GEN.submodels.su01_06_3 3.0
###setting value for variable "Solver->Modules->Spray->General settings for all particles->Submodels->E4"
set-const solver.MO.SP.GEN.submodels.su01_06_4 209000
###setting value for variable "Solver->Modules->Spray->General settings for all particles->Submodels->E5"
set-const solver.MO.SP.GEN.submodels.su01_06_5 7.64e18
###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Wallfilm entrainment->Activate particle introduction from wallfilm"
set-const solver.MO.SP.IN.EN.sprwallfilm 1
###setting value for variable "Solver->Modules->Spray->Particle introduction methods->On Selection->Activate particle introduction from selection"
set-const solver.MO.SP.IN.OS.activate 0

#----------------------------------------Wallfilm
###setting value for variable "Solver->Module activation->Wallfilm"
set-const solver.MA.actWallfilm 1

###setting value for variable "Solver->Modules->Wallfilm->Expert->Max. number of subcycles"
set-const solver.MO.WF.EXP.maxnusub 1000
###setting value for variable "Solver->Modules->Wallfilm->Expert->Evaporation rate limiter"
set-const solver.MO.WF.EXP.ev_mu_02 20.0

###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->Evaporation submodel"
set-const solver.MO.WF.GEN.submodels.Evaporation "SCR-thermolysis"
###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->S2"
set-const solver.MO.WF.GEN.submodels.s_1_01_evap 6
set-const solver.MO.WF.GEN.submodels.s_1_02_evap 64000.000000
###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->S3"
set-const solver.MO.WF.GEN.submodels.s_1_03_evap 100000.000000
set-const solver.MO.WF.GEN.submodels.s_1_04_evap 0

# no precipitation
set-const solver.MO.WF.GEN.submodels.s_1_05_evap 0
###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->Submodel name"
set-const solver.MO.WF.GEN.submodels.SubModelSplash "Kuhnke"
###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->S2      No of splashed parcels"
set-const solver.MO.WF.GEN.submodels.splash_2 3.0
###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->S3      Droplet boiling model (0=off/1=Wruck/2=Birkhold)"
set-const solver.MO.WF.GEN.submodels.splash_3 2.0
###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->S5      4 Regimes=0 / 6 Regimes=1"
set-const solver.MO.WF.GEN.submodels.splash_5 1.0
###setting value for variable "Solver->Modules->Wallfilm->General->Submodels->Min. reflection angle"
set-const solver.MO.WF.GEN.submodels.minReflAngle 2.000000
###setting value for variable "Solver->Modules->Wallfilm->General->Output->HTC_Film/Wall"
set-const solver.MO.WF.GEN.output.ou014 1
set-const solver.MO.WF.GEN.submodels.wallThickness 0

# following for "Solver->Modules->Wallfilm->General->Solver->..."
# Minimum film thickness
set-const solver.MO.WF.GEN.solver.minfilm 1e-7
# Wall shear
set-const solver.MO.WF.GEN.solver.so01 1
# Tke
set-const solver.MO.WF.GEN.solver.so02 1
# Heat transfer
set-const solver.MO.WF.GEN.solver.so03 1
# Temperature
set-const solver.MO.WF.GEN.solver.so04 1
# Evaporation
set-const solver.MO.WF.GEN.solver.so05 1
# Entrainment
set-const solver.MO.WF.GEN.solver.so06 1
# Balancing
set-const solver.MO.WF.GEN.solver.so07 1
# Splashing
set-const solver.MO.WF.GEN.solver.so08 1
# Momentum equation
set-const solver.MO.WF.GEN.solver.so09 1
# Momentum source
set-const solver.MO.WF.GEN.solver.co01 0
# Vapor mass source
set-const solver.MO.WF.GEN.solver.co02 1
# Vapor energy source
set-const solver.MO.WF.GEN.solver.co03 1

###setting value for variable "Solver->Modules->Wallfilm->General->Output->Thickness"
set-const solver.MO.WF.GEN.output.ou01 1
###setting value for variable "Solver->Modules->Wallfilm->General->Output->Relative velocity"
set-const solver.MO.WF.GEN.output.ou02 1
###setting value for variable "Solver->Modules->Wallfilm->General->Output->Wall shear"
set-const solver.MO.WF.GEN.output.ou04 1
###setting value for variable "Solver->Modules->Wallfilm->General->Output->Temperature"
set-const solver.MO.WF.GEN.output.ou05 1
###setting value for variable "Solver->Modules->Wallfilm->General->Output->Evaporation rate"
set-const solver.MO.WF.GEN.output.ou06 1
###setting value for variable "Solver->Modules->Wallfilm->General->Output->HTC_Film/Wall"
set-const solver.MO.WF.GEN.output.ou014 1
###setting value for variable "Solver->Modules->Wallfilm->General->Output->Entrainment rate"
set-const solver.MO.WF.GEN.output.ou07 1
###setting value for variable "Solver->Modules->Wallfilm->General->Output->Impingement"
set-const solver.MO.WF.GEN.output.ou08 1

"""
#Template for nozzle, inputs:
# {0}: Nozzle number
# {1}: X pos
# {2}: Y pos
# {3}: Z pos
# {4}: X dir
# {5}: Y dir
# {6}: Z dir
# {7}: Teilkreisdurchmesser
# {8}: Number of nozzle holes
# {9}: Schirmwinkel
# {10}:Verdrehwinkel des Injektors
# {11}:Start velocity
# {12}:Orifice diameter
# {outer_angle}:half outer cone angle
# {inner_angle}:half inner cone angle
# (soi}:SOI
# {duration}:duration [ms]!!!
# {mass}:mass
# {inner_diam}
SSCNozzleTemplate =r"""
#Following statements are suited for "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[{0}]->"
# Nozzle nr (1,2,...)"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzleNrToCopyFrom 1

# Nozzle name"
set-const solver.MO.SP.IN.NO.NoName[{0}].Name "NoName"

# @tree_title"
#set-const solver.MO.SP.IN.NO.NoName[{0}].tree_title "NoName"
# switch off any submodel
# Nozzle interface->Activation"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzfil.nointer 0
# Nozzle submodels->Radial perturbation"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzsub.ns01 "Disable"
# Nozzle submodels->Nozzle flow simulation"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzsub.ns02 "Disable"
# Nozzle submodels->BOOST Hydraulics interface"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzsub.ns06 "Disable"
# Nozzle submodels->Gas jet"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzsub.ns04 "Disable"

# setting main describing nozzle parameters
# Diagrams->Start velocity"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di01 {11}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Swirl velocity"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di08 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Injection rate"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di02 1

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Outer diameter"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di03 {12}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Inner diameter"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di04 {inner_diam}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Half outer cone angle"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di05 {outer_angle}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Half inner cone angle"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di06 {inner_angle}
###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Particle sizes"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.di07 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Diagrams->Volume based particle size distribution"
set-const solver.MO.SP.IN.NO.NoName[{0}].diagram.volBPSDistr 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->X-coordinate"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge01 {1:.5g}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Y-coordinate"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge02 {2:.5g}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Z-coordinate"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge03 {3:.5g}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->X-direction"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge04 {4:.5g}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Y-direction"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge05 {5:.5g}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Z-direction"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge06 {6:.5g}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Nozzle diameter at hole center positions"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge11 {7}
###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Number of nozzle holes"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge12 {8}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Spray angle delta 1"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge13 {9}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Spray angle delta 2"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge14 {10}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Circumferential hole distribution"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge15 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Spray geometry"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.SprayGeo "Full Spray"

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->X-symmetry"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge07 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Y-symmetry"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge08 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Z-symmetry"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge09 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->Geometry data->Angle"
set-const solver.MO.SP.IN.NO.NoName[{0}].geometry.ge10 0

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->General nozzle data->Start time"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.nostart {soi}

###setting value for variable "Solver->Modules->Spray->Particle introduction methods->Nozzles->Nozzle[1]->General nozzle data->@durfl"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.durfl 1
# General nozzle data->@noend"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.noend 0
# General nozzle data->[ms]"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.nodur {duration}
# General nozzle data->@no03"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.no03 "Mass"
# General nozzle data->Mass in computational domain"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.no03_02 {mass}
# General nozzle data->Fluid temperature"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.notemp 358.15
# General nozzle data->Property set number"
set-const solver.MO.SP.IN.NO.NoName[{0}].nozzdat.noprop 1
"""

#
# {nozzleno}
# {flowratefile}
SSCNozzleFlowRate = r"""
# Diagrams->Injection rate"
set-table solver.MO.SP.IN.NO.NoName[{nozzleno}].diagram.di02 {flowratefile}
"""
#
# {nozzleno}
# {partsizefile}
SSCNozzlePartsize = r"""
# Diagrams->particle sizes"
set-table solver.MO.SP.IN.NO.NoName[{nozzleno}].diagram.di07 {partsizefile}
"""
#
# {nozzleno}
# {partsizefile}
SSCNozzlePartsizeConstant = r"""
# Diagrams->particle sizes"
set-const solver.MO.SP.IN.NO.NoName[{nozzleno}].diagram.di07 {diameter}
"""

ADBLUE_GID = r"""BEGIN
CHANNEL = ['COL0','COL1','COL2']
UNIT = ['','','']
END
        WATER   4       0.675
        UREA    7       0.23284
        UREA    3       0.09216
"""

ADBLUE_GID_SP = r"""BEGIN
CHANNEL = ['COL0','COL1','COL2']
UNIT = ['','','']
END
        WATER   4       0.675
        UREA    7       0.23284
        UREA    3       0.09216
        UREA_SP    7       0.0
        UREA_SP    3       0.0
"""

def __createInclude(firecase):
    """
    Ensures all the needed 2D, 3D and global formula files are available in project directory
    will create subdir include in project dir (where fpr is placed)
    all files from ssf/include will be placed there
    """
    includeDir = os.path.join(firecase.projDir, 'include')

    if not os.path.exists(includeDir):
        os.mkdir(includeDir)

    fire_version_string = ssf.getVersion()
    srcDir = 'include'

    scrfiles = resource_listdir('ssf', srcDir)
#     print scrfiles
    for filename in scrfiles:
        outfname = os.path.join(includeDir, filename)
        if not os.path.exists(outfname):
            srcfilename = resource_filename('ssf', srcDir+'/'+filename)
            shutil.copy(srcfilename, outfname)


def __getTemplateIndex():
    """
    """
    fire_version_string = ssf.getVersion()
    template_index = None
    template_index = json.load(resource_stream('ssf', 'templates_index'))

    return template_index





def createSSC(firecase, selections, timeInfo=None, x = [0,0,0], dx=[0,0,1]):
    """
    firecase is the firecase to modify type(ssf.FireCase)
    selections is a list of tuples [str,           bool,        bool, bool]
                    [selectionName, Evaporation,   UI, Wallfilm]
    timeInfo includes spray.InjectorProperties and spray.TargetMassFlowProperties
    x is the injector location
    dx is injector direction (as per FIRE definition)

    the file ssf/templates_index contains an index all 2D result files given in ssf/include
    and specifies their respective name and unit

    creates a ssc and accompanying gid-files  within the specified case. All settings are
    according to currenct (Aug. 2014) standards for SCR applications
    2D formulas are added according to selections list
    3D formula and global formula for averaging are added

    """
    fire_version = float( ssf.getVersion()[1:].split('.')[0])

    __createInclude(firecase)

    mySSF = ssf.SSFNode.readSSF(firecase.ssfFile)

    #read all existing 2d results specifications
    existing2Dresults = mySSF.OC.W2DOUTPUT.keys()
    oldNum2DResults = len(existing2Dresults)-1

    addSelList = []
    #keep already existing entries
    # attention! If an additional geometry selection formula has been added this will not be taken into account!
    for sel in selections:
        keepSel = sel[1] or sel[2] or sel[3]
        if keepSel:
            if sel[0] in existing2Dresults:
                pass
            else:
                addSelList.append(sel)
    addSelList.sort()

    #prepare the output
    sscContent = StringIO.StringIO()

    #check if global formula is already included
    frmlInGlobal = False
    for formula in mySSF.GFD.keys():
        try:
            frmlInGlobal = frmlInGlobal or "calcRunningSum()" in mySSF.GFD[formula].Formel
        except:
            pass

    #if not - add it
    if not frmlInGlobal:
            sscContent.write(
            SSCFileFrml.format(
                GlobalFormula = os.path.abspath(os.path.join(firecase.projDir,"include","runningSum.frml")),
                numGlFormula = len(mySSF.GFD.keys())+1
            )
        )

    #check for templates given
    #file template index is needed as the name and unit of a 2d result is not stored
    #within the .frml file
    template_index = __getTemplateIndex()

    #add 3D result formulas for averaged species as defined in template_index file
    threeDFormulas = template_index['3D']

    containedThreeDFormulas = list()
    for formula in mySSF.OC.W3DRF.keys():
        if formula.startswith('Formula'):
            containedThreeDFormulas.append(mySSF.OC.W3DRF[formula].Name)

    nThreeDFormulas = mySSF.OC.W3DRF.numFormulasIn3DRes
    threed_result_part = StringIO.StringIO()
    for k, v in threeDFormulas.items():
        if not k in containedThreeDFormulas:
            nThreeDFormulas = nThreeDFormulas + 1
            threed_result_part.write(
                SSCFileResult.format(
                NumFormula = nThreeDFormulas,
                ResultFormula = os.path.abspath(os.path.join(firecase.projDir,"include",v )),
                FormulaName = k
                )
            )
    sscContent.write(SSCFileResult_Header.format( TotNumFormula=nThreeDFormulas ))
    sscContent.write( threed_result_part.getvalue() )

    if len(addSelList)>0:
        sscContentLater = StringIO.StringIO()

        sscTemplate = Template(SSCFile2DResult_Header)
        sscContent.write(sscTemplate.substitute(
            NumSelectionsFor2DResults = oldNum2DResults + len(addSelList)
        ))
        i = oldNum2DResults + 1
        sscTemplate = Template(SSCFile2DResult)
        sscTemplateFrml = Template(SSCFile2DResult_Formula)
        sscTemplateFrmlFile = Template(SSCFile2DResult_Formula_Body)
        for sel in addSelList:
            numAddedFrmls = 0
            if sel[1] and sel[4]=='Cell': numAddedFrmls += len(template_index['EVAP'])
            if sel[2]: numAddedFrmls += len(template_index['UI'])
            if sel[3] and sel[4]=='Face': numAddedFrmls += len(template_index['WALLFILM'])
            sscContent.write(sscTemplate.substitute(
                SelectionIndex = i,
                NumFormulas = numAddedFrmls,
                SelectionName = sel[0]
            ))
            j = 1
            if sel[1] and sel[4]=='Cell':
                for name, filename in template_index['EVAP'].items():
                    sscContent.write(sscTemplateFrml.substitute(
                        SelectionIndex = i,
                        Frml2DResultsIndex = j
                    ))
                    sscContentLater.write(sscTemplateFrmlFile.substitute(
                        SelectionIndex = i,
                        Frml2DResultsIndex = j,
                        PathToFrml = os.path.join(firecase.projDir, 'include', filename),
                        FrmlName = name
                    ))
                    j += 1
            if sel[2]:
                for name, filename in template_index['UI'].items():
                    sscContent.write(sscTemplateFrml.substitute(
                        SelectionIndex = i,
                        Frml2DResultsIndex = j
                    ))
                    sscContentLater.write(sscTemplateFrmlFile.substitute(
                        SelectionIndex = i,
                        Frml2DResultsIndex = j,
                        PathToFrml = os.path.join(firecase.projDir, 'include', filename),
                        FrmlName = name
                    ))
                    j += 1
            if sel[3] and sel[4]=='Face':
                for name, filename in template_index['WALLFILM'].items():
                    sscContent.write(sscTemplateFrml.substitute(
                        SelectionIndex = i,
                        Frml2DResultsIndex = j
                    ))
                    sscContentLater.write(sscTemplateFrmlFile.substitute(
                        SelectionIndex = i,
                        Frml2DResultsIndex = j,
                        PathToFrml = os.path.join(firecase.projDir, 'include', filename),
                        FrmlName = name
                    ))
                    j += 1
            i += 1
        sscContent.write(sscContentLater.getvalue())
        del sscContentLater


    #enable 3d output of mole fractions
    sscContent.write(SSCSpeciesResult)

    #add cell selections defined for UI for accumulated species mass fluxes
    existingSpeciesFrmls = mySSF.MO.ST.ST2D.keys()
    numSel = len(existingSpeciesFrmls)
    for sel in selections:
        if sel[2] and sel[4]=='Cell':
            if sel[0] in existingSpeciesFrmls:
                #won't check for selected values
                pass
            else:
                sscContent.write(SSCSpecies2DResult.format(numSel, sel[0] ))
                numSel = numSel + 1

    #add cell selections defined for evaporation and add spray values
    existingSpray2DResults = mySSF.MO.SP.GEN.output1.keys()
    numSel = len(existingSpray2DResults)
    for sel in selections:
        if sel[1] and sel[4]=='Cell':
            if sel[0] in existingSpray2DResults:
                #won't check for selected values
                pass
            else:
                sscContent.write(SSCSpray2DResult.format(numSel, sel[0] ))
                numSel = numSel + 1



    #global spray settings
    adblue_fp = open(os.path.join(firecase.caseDir, 'AdBlue.gid'), 'w')
    adblue_fp.write(ADBLUE_GID)
    adblue_fp.close()
    sscContent.write(SSCSprayGlobals.format( os.path.join(firecase.caseDir, 'AdBlue.gid') ))

    #time stepping, 3d results, backups, *Nozzle*!
    if timeInfo != None:

        threeD = open(os.path.join(firecase.caseDir, 'threed.gid'), 'w' )
        if fire_version < 2014:
            threeD.write("BEGIN\nCHANNEL = ['upto/at','time','each']\nUNIT = ['','s','s']\nEND\n")
        else:
            threeD.write("BEGIN\nCHANNEL = ['upto/at','time','Output Frequency']\nUNIT = ['','s','s']\nEND\n")

        for i in range(len(timeInfo.t3)):
            threeD.write( " upto\t%g\t%g\n" % (timeInfo.t3[i], timeInfo.res[i]  ))
        threeD.close()

        backup = open(os.path.join(firecase.caseDir,"backup.gid"), 'w')
        if fire_version < 2014:
            backup.write("BEGIN\nCHANNEL = ['upto/at','time','each']\nUNIT = ['','s','s']\nEND\n")
        else:
#            backup.write("BEGIN\nCHANNEL = ['upto/at','time','Output Frequency']\nUNIT = ['','s','s']\nEND\n")
            backup.write("BEGIN\nCHANNEL = ['COL0','COL1','COL2']\nUNIT = ['','s','s']\nEND\n")
        for i in range(len(timeInfo.t2)):
            backup.write(' upto\t%g\t%g\n' % (timeInfo.t2[i],timeInfo.t2[i] ) )

        backup.close()


        dtfile = open(os.path.join(firecase.caseDir,"timestep.gid"), 'w')
        dtfile.write("BEGIN\nCHANNEL = ['upto','time','DeltaT']\nUNIT = ['','s','s']\nEND\n")
        for i in range(len(timeInfo.t1)):
            dtfile.write(" upto\t%g\t%g\n" % (timeInfo.t1[i], timeInfo.dt[i]))

        sscContent.write( SSCTimestepInfo.format(
             timeInfo.total_duration,
             os.path.join(firecase.caseDir, 'timestep.gid'),
             os.path.join(firecase.caseDir, 'threed.gid'),
             os.path.join(firecase.caseDir, 'backup.gid') ) )

        DURATION= 0
        MASS = 0
        addlNozzle=0
        if timeInfo.targetProps.single_nozzle:
            addlNozzle = 1
            DURATION = timeInfo.duration
            MASS = timeInfo.props.mass_per_shot.sval*timeInfo.numInjections

            flowrateFile = open(os.path.join(firecase.caseDir, 'flowrate.gid'), 'w')
            flowrateFile.write("BEGIN\nCHANNEL = ['Number','di02']\nUNIT = ['',' ']\nEND'")
            for i in range(len(timeInfo.t)):
                flowrateFile.write( '\n{:>12} {:>12}'.format(timeInfo.t[i], timeInfo.m[i]))
            flowrateFile.close()
        else:
            addlNozzle = timeInfo.numInjections
            DURATION = timeInfo.opentime
            MASS = timeInfo.props.mass_per_shot.sval

        sscContent.write( """# delete all previously contained nozzles
set-const solver.MO.SP.IN.NO.numno {0}
""".format(addlNozzle) )

        inner_diam = 0
        inner_angle = 0
        if timeInfo.props.hollow_cone:
            inner_diam = timeInfo.props.inner_diam.sval
            inner_angle = toDegree(timeInfo.props.inner_half_angle)

        partsize = False
        partsizefile = None
        constpartsize = False

        if timeInfo.props.particlesize_constant:
            constpartsize = True

        elif timeInfo.props.particlesize_fname is not None and len(timeInfo.props.particlesize_fname)>0:
            try:
                d, p = spray.loadParticlesSizes(timeInfo.props.particlesize_fname)
                if len(d) > 0:
                    partsizefile = open(os.path.join(firecase.caseDir, 'partsizes.gid'), 'w')
                    partsizefile.write("BEGIN\nCHANNEL = ['Size','Probability']\nUNIT = ['mym','']\nEND'")
                    for i in range(len(d)):
                        partsizefile.write( '\n{:>12} {:>12}'.format(d[i], p[i]))
                    partsizefile.close()
                    partsize = True
            except IOError:
                partsizefile = None
            except ValueError:
                pass
        #maybe directly saved as adjunct data for the injector
        elif timeInfo.props.adjunct.get('diameters', None) is not None:
            d = timeInfo.props.adjunct.get('diameters', None)
            p = timeInfo.props.adjunct.get('probabilities', None)
            if d is not None and p is not None and len(d) > 0:
                partsizefile = open(os.path.join(firecase.caseDir, 'partsizes.gid'), 'w')
                partsizefile.write("BEGIN\nCHANNEL = ['Size','Probability']\nUNIT = ['mym','']\nEND'")
                for i in range(len(d)):
                    partsizefile.write( '\n{:>12} {:>12}'.format(d[i], p[i]))
                partsizefile.close()
                partsize = True


        for i in range(addlNozzle):
            SOI = timeInfo.initial_pause + timeInfo.t[ (i)*4 ]
            sscContent.write(  SSCNozzleTemplate.format( i+1,
                x[0],x[1],x[2],dx[0],dx[1],dx[2],
                timeInfo.props.nozzle_diameter.sval,
                timeInfo.props.number_nozzles,
                toDegree(timeInfo.props.spray_angle1),
                toDegree(timeInfo.props.spray_angle2),
                timeInfo.props.start_velo.sval,
                timeInfo.props.outer_diam.sval,
                outer_angle = toDegree(timeInfo.props.outer_half_angle),
                inner_angle=inner_angle,
                soi=SOI, duration=DURATION*1e3,mass=MASS,
                inner_diam=inner_diam
            ))
            if(timeInfo.targetProps.single_nozzle):
                sscContent.write( SSCNozzleFlowRate.format( nozzleno=i+1, flowratefile= os.path.join(firecase.caseDir, 'flowrate.gid')))
            if partsize and partsizefile is not None :
                sscContent.write(SSCNozzlePartsize.format(nozzleno = i+1, partsizefile = os.path.join(firecase.caseDir, 'partsizes.gid')))
            if constpartsize:
                sscContent.write(SSCNozzlePartsizeConstant.format(nozzleno= i+1, diameter = timeInfo.props.particlesize_diam.sval))
    sscFilename = os.path.join(firecase.caseDir, 'scr.ssc')
    sscFile = open(sscFilename, 'w')
    sscFile.write(sscContent.getvalue())
    sscFile.close()
    return sscFilename
