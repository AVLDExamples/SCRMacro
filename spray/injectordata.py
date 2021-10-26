#!/usr/bin/env python
#
# v1.1.2
# SCRMacro for FIRE_WM v2017
# author: C. Schmalhorst
# (C) AVL Deutschland GmbH
# @date=20170322
# @version=112
#
import act
from act.util import OrderedDict
import act.serial
import act.ui
import act.units
import act.unitcustom
from act.boxed import Enum, defenum
import dm
import os.path
from act.serial import dump
import base64

MassflowAmount = act.units.amount_type('massflow')
MassAmount = act.units.amount_type('mass')
TimeAmount = act.units.amount_type('time')
LengthAmount = act.units.amount_type('length')
AngleAmount = act.units.amount_type('angle')
FrequencyAmount = act.units.amount_type('frequency')
VelocityAmount = act.units.amount_type('velocity')
defenum('inj_typedef', ('pwm', 'fm'))

class InjectorProperties(act.Base):
    """
    class to define an injector as needed by the ssf
    location is not saved - only rotation wrt. local coord system
    no spray submodels possible / injector as for SCR applications
    """
    formatter = OrderedDict([
                             ('pwm', 'pulse width modulation (constant frequency)'),
                             ('fm',  'frequency modulation (constant mass/shot)')
                             ])

    act.namespace.defclass
    defslot('injector_type', inj_typedef, 'pwm' )
    #----------------------------------------------------------
    defslot('full_massflow', MassflowAmount, 3200, 'massflow~g_h')
    defslot('frequency', FrequencyAmount, 4, 'frequency~Hz')
    #----------------------------------------------------------
    defslot('mass_per_shot', MassAmount, 12.5, 'mass~mg')
    defslot('shot_duration', TimeAmount, 15, 'time~ms')
    #----------------------------------------------------------
    defslot('number_nozzles', int, 3)
    defslot('nozzle_diameter', LengthAmount, 1.5, 'length~mm')
    defslot('spray_angle1', AngleAmount, 10, 'angle~deg')
    defslot('spray_angle2', AngleAmount, 0, 'angle~deg')
    defslot('start_velo', VelocityAmount, 24, 'velocity~m_s' )
    defslot('outer_diam', LengthAmount, 100, 'length~mym')
    defslot('outer_half_angle', AngleAmount, 7, 'angle~deg')
    defslot('hollow_cone', bool, False)
    defslot('inner_half_angle', AngleAmount, 4, 'angle~deg')
    defslot('inner_diam', LengthAmount, 50, 'length~mym')
    defslot('particlesize_fname', str)
    defslot('particlesize_constant', bool, True)
    defslot('particlesize_diam', LengthAmount, 70, 'length~mym')

class TargetMassFlowProperties(act.Base):
    act.namespace.defclass
    defslot('massflow', MassflowAmount, 1200, 'massflow~g_h')
    defslot('min_duration', TimeAmount, 1,'time~s')
    defslot('min_injections', int,3)
    defslot('single_nozzle', bool, False)
    defslot('initial_pause', TimeAmount, 50, 'time~ms')
    defslot('quantize', bool, True)
    defslot('quantize_raster', TimeAmount, 0.1, 'time~ms')
    defslot('spray_present', TimeAmount, 20, 'time~ms')
    defslot('extend_dt', bool, True)


class Storage:

    @staticmethod
    def __get_targetdir():
        """
        Needed to find the os-specific location of the SCRNozzles directory
        """

        targetDir = None
        if os.name is 'nt':
            targetDir = os.path.join(os.getenv('APPDATA'), 'AVL', 'AVL FIRE WM')
        else:
            targetDir = os.path.expanduser("~/.avl/avl fire wm")

        scrnozzledir = os.path.join(targetDir, 'SCRNozzles')
        if not os.path.exists(scrnozzledir):
            os.makedirs(scrnozzledir)
        return scrnozzledir
    @staticmethod
    def store_nozzle(injectorProperties, name):
        """
        Used to store act.serial.dump'able data to a hard coded directory:
            on Linux: ~/.avl/avl fire wm/SCRNozzles/
            on Windows: %APPDATA%\AVL\AVL FIRE WM\SCRNoccles
        name will be b64-encoded and used as filename, + extension '.scrnozzle'
        """
        nname = name
        targetname = os.path.join(Storage.__get_targetdir(), base64.urlsafe_b64encode(name)+'.scrnozzle')

        if os.path.exists(targetname):
            i = 1
            freeNameFound = False
            while not freeNameFound:
                nname = name +' '+ str(i)
                targetname = os.path.join(Storage.__get_targetdir(), base64.urlsafe_b64encode(nname)+'.scrnozzle')
                if os.path.exists(targetname):
                    i = i+1
                else:
                    freeNameFound = True

        with open(targetname, 'w') as f_out:
            act.serial.dump(injectorProperties,f_out, format=act.serial.Format.XML,xml_indent=True )

        return nname
    @staticmethod
    def get_nozzle(name):
        """
        Used to act.serial.load the object stored in the SCRNozzles dir
            on Linux: ~/.avl/avl fire wm/SCRNozzles/
            on Windows: %APPDATA%\AVL\AVL FIRE WM\SCRNozzles
        the name will be b64_encoded to create the file name
        returns None if the file is not present
        Warning: directory will be created!
        """
        targetname = os.path.join(Storage.__get_targetdir(), base64.urlsafe_b64encode(name)+'.scrnozzle')
        with open(targetname, 'r') as f_in:
            return act.serial.load(f_in)
        return None
    @staticmethod
    def get_stored_nozzles():
        """
        Used to look up files stored in a hard coded directory:
            on Linux: ~/.avl/avl fire wm/SCRNozzles/
            on Windows: %APPDATA%\AVL\AVL FIRE WM\SCRNozzles
        The extension used to filter the results is '.scrnozzle'
        The file name will be b64-decoded and inserted into the list
        Warning: directory will be created!
        """
        targetdir = Storage.__get_targetdir()
        dircontent = os.listdir(targetdir)
        files = []
        for filename in dircontent:
            if filename.endswith('.scrnozzle'):
                files.append(base64.urlsafe_b64decode(filename[:-10]))
        files.sort()
        return files

    @staticmethod
    def __get_stored():
        targetdir = Storage.__get_targetdir()
        dircontent = os.listdir(targetdir)
        files = dict()
        for filename in dircontent:
            if filename.endswith('.scrnozzle'):
                files[base64.urlsafe_b64decode(filename[:-10])] = filename
        return files

    @staticmethod
    def delete_nozzle(name):
        files = Storage.__get_stored()
        if name in files.keys():
            os.remove(os.path.join(Storage.__get_targetdir(),files[name]))

    @staticmethod
    def rename_nozzle(oldname, newname):
        files = Storage.__get_stored()
        if oldname in files.keys():
            nname = newname
            if nname in files.keys():
                i = 1
                freeNameFound = False
                while not freeNameFound:
                    nname = newname +' '+ str(i)
                    if nname in files.keys():
                        i = i+1
                    else:
                        freeNameFound = True

            opath = os.path.join(Storage.__get_targetdir(), files[oldname])
            npath = os.path.join(Storage.__get_targetdir(), base64.urlsafe_b64encode(nname )+ '.scrnozzle')
            os.rename(opath, npath)
            return nname
