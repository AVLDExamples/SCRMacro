#!/usr/bin/env python
#
# v1.1.2
# SCRMacro for FIRE_WM v2017
# author: C. Schmalhorst
# (C) AVL Deutschland GmbH
# @date=20170322
# @version=112
#

import gtk
import math
import spray
import matplotlib
import numpy as np
matplotlib.use('GtkAgg')
import matplotlib.pyplot
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as Canvas
from spray import InjectorProperties, TargetMassFlowProperties, Storage
from wmhelper import SelColumn
import os.path
import act
import act.ui
import ui
import act.units
import act.unitcustom
import dm

DECIMALS = 4
MIN_NUMBER_OF_TIMESTEPS_INJECTOR = 20
TARGET_TIME_STEP_WET = 0.001
TARGET_TIME_STEP_DRY = 0.005


class UnitContextFixed(act.ui.Context):
    act.namespace.defclass
    defslot('unit_repo')

    def __init__(self, length_unit=act.units.find('length~mm'),
                 angle_unit=act.units.find('angle~deg'),
                 massflow_unit=act.units.find('massflow~g_h'),
                 time_unit=act.units.find('time~ms'),
                 mass_unit=act.units.find('mass~mg'),
                 frequency_unit=act.units.find('frequency~Hz'),
                 velo_unit=act.units.find('velocity~m_s')):
        super(UnitContextFixed, self).__init__()
        groups = dm.List()
        group_length = act.unitcustom.CustomUnitGroup('length')
        group_length.default_unit = length_unit
        groups.append(group_length)
        group_angle = dm.CustomUnitGroup(dm.unit_group('angle'), unit_list=act.List([act.units.find('angle~deg'), act.units.find('angle~rad')]))
        group_angle.default_unit = angle_unit
        groups.append(group_angle)
        cgrp = act.unitcustom.CustomUnitGroup('massflow')
        cgrp.default_unit = massflow_unit
        groups.append(cgrp)
        cgrp = act.unitcustom.CustomUnitGroup('time')
        cgrp.default_unit = time_unit
        groups.append(cgrp)
        cgrp = act.unitcustom.CustomUnitGroup('mass')
        cgrp.default_unit = mass_unit
        groups.append(cgrp)
        cgrp = act.unitcustom.CustomUnitGroup('frequency')
        cgrp.default_unit = frequency_unit
        groups.append(cgrp)
        cgrp = act.unitcustom.CustomUnitGroup('velocity')
        cgrp.default_unit = velo_unit
        groups.append(cgrp)

#        groups[0].default_unit = length_unit #act.units.find('length~m')
#        groups[0].group._units = [act.units.find('length~m'), act.units.find('length~mm'), act.units.find('length~yd'), act.units.find('length~ft'), act.units.find('length~in')]#act bug workaround
#        groups[1].default_unit = angle_unit #act.units.find('angle~deg')
#        groups[1].group._units = [act.units.find('angle~deg'), act.units.find('angle~rad')] #act bug workaround
        self.unit_repo = act.unitcustom.CustomUnitRepo(groups)


class InjectorPropertiesEditor(act.ui.CompositeEditor):
    def __init__(self):
        layout = act.ui.VLDesc(directives={'resizex': False}, members=[
            act.ui.FormDesc('injector_type_ed', act.ui.EnumSelector('Injector type:', formatter=InjectorProperties.formatter.get, selection_widget=act.ui.SelectionWidget.RADIO)),
            act.ui.FormDesc('full_massflow_ed', act.ui.AmountEditor(labeltext='Full massflow')),
            act.ui.FormDesc('frequency_ed', act.ui.AmountEditor(labeltext='Injector frequency')),
            act.ui.FormDesc('mass_per_shot_ed', act.ui.AmountEditor(labeltext='Mass injected per shot')),
            act.ui.FormDesc('shot_duration_ed', act.ui.AmountEditor(labeltext='Duration per shot')),
            act.ui.FormDesc('number_nozzles', act.ui.IntEditor(labeltext='Number of orifices')),
            act.ui.FormDesc('nozzle_diameter', act.ui.AmountEditor(labeltext='Orifices are on radius of')),
            act.ui.FormDesc('spray_angle1', act.ui.AmountEditor(labeltext='Spray axis direction')),
            act.ui.FormDesc('spray_angle2', act.ui.AmountEditor(labeltext='Injector rotation')),
            act.ui.FormDesc('start_velo', act.ui.AmountEditor(labeltext='Start Velocity')),
            act.ui.FormDesc('outer_diam', act.ui.AmountEditor(labeltext='Orifice diameter')),
            act.ui.FormDesc('outer_half_angle', act.ui.AmountEditor(labeltext='Half angle of one spray cone')),
            act.ui.FormDesc('hollow_cone', act.ui.BoolEditor(labeltext='hollow cone injector')),
            act.ui.FormDesc('inner_diam_ed', act.ui.AmountEditor(labeltext='inner orifice diameter')),
            act.ui.FormDesc('inner_half_angle_ed', act.ui.AmountEditor(labeltext='Hollow cone angle')),
        ])
        linker_rules = [
          '@.injector_type->injector_type_ed.@' ,
          '@.full_massflow->full_massflow_ed.@' ,
          '@.frequency->frequency_ed.@' ,
          '@.mass_per_shot->mass_per_shot_ed.@' ,
          '@.shot_duration->shot_duration_ed.@' ,
          '@.inner_diam->inner_diam_ed.@' ,
          '@.inner_half_angle->inner_half_angle_ed.@' ,
        ]
        property_rules = [
            act.ui.VisibleRule('full_massflow_ed', lambda s: s.target.injector_type.value == 'pwm'),
            act.ui.VisibleRule('frequency_ed', lambda s: s.target.injector_type.value == 'pwm'),
            act.ui.VisibleRule('mass_per_shot_ed', lambda s: s.target.injector_type.value == 'fm'),
            act.ui.VisibleRule('shot_duration_ed', lambda s: s.target.injector_type.value == 'fm'),
            act.ui.EnabledRule('inner_diam_ed', lambda s: s.target.hollow_cone),
            act.ui.EnabledRule('inner_half_angle_ed', lambda s: s.target.hollow_cone),
        ]
        content_rules = [
            act.ui.ChangedRule('injector_type_ed', self.inj_change),
        ]
        super(InjectorPropertiesEditor, self).__init__(layout=layout, linker_rules=linker_rules, property_rules=property_rules, content_rules=content_rules)
        self.context = UnitContextFixed()

    def inj_change(self, ev=None, obj=None):
        return

class Prefs:
    pass



class InjectorParticlePropertiesEditor(act.ui.CompositeEditor):

    prefs = Prefs()

    def __init__(self):
        fname_editor = act.ui.FilenameEditor(
                labeltext='Particle Size file',
                filters=[('DAT files', '*.dat'), ('TXT files', '*.txt'), ('GIDAS files', '*.gid')],
                must_exist=True)

        # global PM_GetProjectIOData

        self.prefs.lastdir = os.path.curdir

        fname_editor.file_chooser_prefs = lambda ed : self.prefs

        layout = act.ui.VLDesc(directives={'resizex': False}, members=[
            act.ui.FormDesc('particlesize_constant', act.ui.BoolEditor(labeltext='set constant particle size')),
            act.ui.FormDesc('particlesize_diam', act.ui.AmountEditor(labeltext='Particle Diameter')),
            act.ui.FormDesc('particlesize_fname', fname_editor),
        ])
        property_rules = [
            act.ui.EnabledRule('particlesize_diam', lambda s: s.target.particlesize_constant),
            act.ui.EnabledRule('particlesize_fname', lambda s: not s.target.particlesize_constant),
        ]
        super(InjectorParticlePropertiesEditor, self).__init__(layout=layout, property_rules=property_rules)
        self.context = UnitContextFixed(length_unit=act.units.find('length~mym'))

class TargetMassFlowPropertiesEditor(act.ui.CompositeEditor):
    def __init__(self):
        layout = act.ui.VLDesc(members=[
            act.ui.FormDesc('massflow_ed', act.ui.AmountEditor(labeltext='AdBlue massflow')),
            act.ui.FormDesc('min_duration_ed', act.ui.AmountEditor(labeltext='minimum sim. duration')),
            act.ui.FormDesc('min_injections_ed', act.ui.IntEditor(labeltext='minimum no. of injections')),
            act.ui.FormDesc('single_nozzle_ed', act.ui.BoolEditor(labeltext='single ssf Nozzle')),
            act.ui.FormDesc('initial_pause_ed', act.ui.AmountEditor(labeltext='Pause before injection')),
            act.ui.FormDesc('quantize_ed', act.ui.BoolEditor(labeltext='Quantize')),
            act.ui.FormDesc('quantize_raster_ed', act.ui.AmountEditor(labeltext='Quantization raster')),
            act.ui.FormDesc('extend_dt_ed', act.ui.BoolEditor(labeltext='Extend dT')),
            act.ui.FormDesc('spray_present_ed', act.ui.AmountEditor(labeltext='Add wet state')),
                    ])
        linker_rules = [
          '@.massflow->massflow_ed.@' ,
          '@.min_duration->min_duration_ed.@' ,
          '@.min_injections->min_injections_ed.@' ,
          '@.single_nozzle->single_nozzle_ed.@' ,
          '@.initial_pause->initial_pause_ed.@' ,
          '@.quantize->quantize_ed.@' ,
          '@.quantize_raster->quantize_raster_ed.@' ,
          '@.spray_present->spray_present_ed.@' ,
          '@.extend_dt->extend_dt_ed.@' ,
          ]
        property_rules = [
            act.ui.VisibleRule('quantize_raster_ed', lambda s: s.target.quantize),
            act.ui.VisibleRule('spray_present_ed', lambda s: s.target.extend_dt),
        ]
        super(TargetMassFlowPropertiesEditor, self).__init__(layout=layout, linker_rules=linker_rules, property_rules=property_rules)
        self.context = UnitContextFixed()

class CaseSelection(gtk.VBox):
    def __init__(self, caselist, projname):
        super(CaseSelection, self).__init__()

        label = gtk.Label('Available Cases in ' + projname)
        self.pack_start(label, fill=False, expand=False)

        button = None
        self.selectedCase = caselist[0]
        self.callback = None
        for selected_name in caselist:
            button = gtk.RadioButton(button, selected_name[0:-6], use_underline=False)
            button.connect('toggled', self.on_toggled, selected_name)
            self.pack_start(button, False, False, 3)


    def on_toggled(self, button, selected_name):
        if button.get_active():
            self.selectedCase = selected_name
            if not self.callback is None:
                self.callback()

class SelectionSelection(gtk.VBox):



    class SelEditor(ui.CompositeEditor):
        def __init__(self):
            super(SelectionSelection.SelEditor, self).__init__(
                layout=ui.VLDesc([
                    ui.FormDesc(
                        'mixed',
                        ui.ListEditor((
                            ui.ListColDesc( SelColumn.Selection, readonly=True, caption='Selection'),
                            ui.ListColDesc( SelColumn.Evaporation, readonly=False, caption='Evaporation'),
                            ui.ListColDesc( SelColumn.UI, readonly=False, caption='UI'),
                            ui.ListColDesc( SelColumn.Wallfilm, readonly=False, caption='Wallfilm'),
                            ui.ListColDesc( SelColumn.SelType, readonly=True, caption='Selection Type'),
                        )),
                        directives=dict(resizex=True, resizey=True),
                    ),
                ], directives=dict(resizex=True, resizey=True),)
            )

    _colnames = ["Selection", "Evaporation", "UI", "Wallfilm", "SelType" ]

    def __init__(self):
        super(SelectionSelection, self).__init__()

        label = gtk.Label('You can select face selections for inserting wallfilm-related 2D results, cell selections for evaporation and spray related 2D results and either cell or face selections for uniformity informations (UI)')
        label.set_line_wrap(True)
        self.pack_start(label, False, False, 5)
        self._add_results_checkbutton = gtk.CheckButton('Insert 2D Results')
        self._add_results_checkbutton.set_active(True)
        self.pack_start(self._add_results_checkbutton, False, False, 5)

        self.liststore = dm.List()

        selEditor = SelectionSelection.SelEditor()

        selEditor.subforms.mixed.target = self.liststore
        ui.editor.prepare_linked(selEditor)

        self.pack_start(selEditor.widgets.frame, fill=True, expand=True, padding=1)

#        self.liststore = gtk.ListStore(str, bool, bool, bool, str)
#        self._treeview = gtk.TreeView(self.liststore)

#        columns = []

#        for col in self._colnames:
#            columns.append(gtk.TreeViewColumn(col))
#            self._treeview.append_column(columns[-1])

#        cell = gtk.CellRendererText()
#        columns[0].pack_start(cell, False)
#        columns[0].add_attribute(cell, "text", 0)

#        cellrenderer_toggle = gtk.CellRendererToggle()
#        columns[1].pack_start(cellrenderer_toggle, True)
#        columns[1].add_attribute(cellrenderer_toggle, "active", 1)
#        cellrenderer_toggle.connect("toggled", self.cell_toggledEvap, self.liststore)

#        cellrenderer_toggle = gtk.CellRendererToggle()
#        columns[2].pack_start(cellrenderer_toggle, True)
#        columns[2].add_attribute(cellrenderer_toggle, "active", 2)
#        cellrenderer_toggle.connect("toggled", self.cell_toggledUI, self.liststore)

#        cellrenderer_toggle = gtk.CellRendererToggle()

#        columns[3].pack_start(cellrenderer_toggle, True)
#        columns[3].add_attribute(cellrenderer_toggle, "active", 3)
#        cellrenderer_toggle.connect("toggled", self.cell_toggledWF, self.liststore)

#        cell = gtk.CellRendererText()
#        columns[4].pack_start(cell, False)
#        columns[4].add_attribute(cell, "text", 4)

#        scrolled_window = gtk.ScrolledWindow()
#        scrolled_window.add(self._treeview)
#        scrolled_window.set_size_request(250, 400)
 #       self.pack_start(scrolled_window, expand=True, fill=True)

    def cell_toggledEvap(self, widget, path, model):
        if not model[path][1] is None:
            model[path][1] = not model[path][1]

    def cell_toggledUI(self, widget, path, model):
        model[path][2] = not model[path][2]

    def cell_toggledWF(self, widget, path, model):
        model[path][3] = not model[path][3]

    def is_add_frml(self):
        return self._add_results_checkbutton.get_active()

# class PWMWidget(gtk.VBox):
#     def __init__(self, *args, **kwargs):
#         gtk.VBox.__init__(self, *args, **kwargs)
#
#         label = gtk.Label('Pulse width modulation setup')
#         self.pack_start(label, False,False, 5)
#         hbox =  gtk.HBox()
#         label = gtk.Label('nominal massflow, fully opened')
#         hbox.pack_start(label, False,False,5)
#         self.pack_start(hbox, expand = False, fill=True, padding = 10)

class SpraySelection(gtk.VBox):
    def __init__(self, *args, **kwargs):
        gtk.VBox.__init__(self, *args, **kwargs)

        self.injectorKnownVBox = gtk.VBox()
        label = gtk.Label('There are selections that mark an injector position.')
        label.set_line_wrap(True)
        self.injectorKnownVBox.pack_start(label, False, False, 5)
        self.add_nozzle_checkbutton = gtk.CheckButton('Add nozzle position based on selection')
        self.add_nozzle_checkbutton.set_active(True)
        self.injectorKnownVBox.pack_start(self.add_nozzle_checkbutton, False, False, 5)
        self.selection_dropdown = gtk.combo_box_new_text()
        self.injectorKnownVBox.pack_start(self.selection_dropdown, False, False, 5)
        self.injectorUnknownVBox = gtk.VBox()
        label = gtk.Label('There is no selection indicating an injector position. location will be set to [0,0,0], direction to [0,0,1]')
        label.set_line_wrap(True)
        self.injectorUnknownVBox .pack_start(label, False, False, 5)

        self.pack_start(self.injectorKnownVBox, expand=False, fill=False, padding=5)
        self.pack_start(self.injectorUnknownVBox, expand=False, fill=False, padding=5)

        sep = gtk.HSeparator()
        self.pack_start(sep, True, True, 5)

        vbox = gtk.HBox()
        vbox.pack_start(gtk.Label('predefined injectors:'), expand=False, fill=False, padding=5)
        self.predefined_injector_dropdown = gtk.combo_box_new_text()
        self.nozzlenames = spray.Storage.get_stored_nozzles()
        self.predefined_injector_dropdown.connect('changed', self.injector_selected)
        vbox.pack_start(self.predefined_injector_dropdown, expand=False, fill=False, padding=5)
        self.pack_start(vbox, expand=False, fill=False, padding=5)
        self.pwmPropsEditor = InjectorPropertiesEditor()

        self.setInjectorProps(InjectorProperties())
#         self.injectorProperties = InjectorProperties()
#          self.pwmPropsEditor.target = self.injectorProperties
#         act.ui.editor.prepare_linked(self.pwmPropsEditor)
        self.pwmWidget = self.pwmPropsEditor.widgets.frame

        self.pack_start(self.pwmWidget, True, True, 10)

    def populate_injector_dropdown(self):
        self.predefined_injector_dropdown.get_model().clear()
        self.nozzlenames = spray.Storage.get_stored_nozzles()
        if len(self.nozzlenames) > 0:
            for nozzlename in self.nozzlenames:
                self.predefined_injector_dropdown.append_text(nozzlename)
            self.predefined_injector_dropdown.connect('changed', self.injector_selected)


    def injector_selected(self, combobox):
        activetext = combobox.get_active_text()
        if activetext is not None:
            injector = spray.Storage.get_nozzle(activetext)
            if injector is not None:
                self.setInjectorProps(injector)

    def set_selections(self, selections):
        self.injectorList = []
        self.selection_dropdown.get_model().clear()

        if not selections is None:
            for sel in selections:
                if 'inj' in sel.lower():
                    self.injectorList.append(sel)

        if len(self.injectorList) > 0:
            self.injectorKnownVBox.show()
            self.injectorUnknownVBox.hide()
            for sel in self.injectorList:
                self.selection_dropdown.append_text(sel)
            self.selection_dropdown.set_active(0)
        else:
            self.injectorKnownVBox.hide()
            self.injectorUnknownVBox.show()

    def setInjectorProps(self, injectorProps):
        self.injectorProperties = injectorProps
        self.pwmPropsEditor.target = self.injectorProperties
        act.ui.editor.prepare_linked(self.pwmPropsEditor)

    def getDosingProperties(self):
        return self.injectorProperties

    def getNozzlePosition(self):
        if self.injectorKnownVBox.get_visible() and self.add_nozzle_checkbutton.get_active():
            return self.injectorList[self.selection_dropdown.get_active()]
        else:
            return None

class TargetMassflowSelection(gtk.VBox):
    def __init__(self, *args, **kwargs):
        gtk.VBox.__init__(self, *args, **kwargs)
        self.massflowProperties = TargetMassFlowProperties()

        self.targetMFlowProperties = TargetMassFlowProperties()
        self.targetMFlowPropsEditor = TargetMassFlowPropertiesEditor()
        self.targetMFlowPropsEditor.target = self.targetMFlowProperties
        act.ui.editor.prepare_linked(self.targetMFlowPropsEditor)
        self.pack_start(self.targetMFlowPropsEditor.widgets.frame, False, False, 10)

class SprayDosingSelection(gtk.VBox):

    def __init__(self, *args, **kwargs):
        gtk.VBox.__init__(self, *args, **kwargs)
        self.figure = matplotlib.pyplot.figure()
        self.axes = self.figure.add_subplot(1, 1, 1)
#        self.axes.set_axis_bgcolor('white')
        # self.axes.set_aspect('equal')
        self.canvas = Canvas(self.figure)
        # self.canvas.set_size_request(200,200)
        self.pack_start(self.canvas, expand=True, fill=True, padding=0)
        self.targetProps = None
        self.props = None

    def setProperties(self, props, targetProps):
        self.props = props
        self.targetProps = targetProps
        self.t = []
        self.m = []
        self.t1 = []
        self.dt = []
        self.t2 = []
        self.bckup = []
        self.t3 = []
        self.res = []
        self.axes.cla()
        if props != None and targetProps != None:
            if props.injector_type.value == 'fm':
                # frequency modulated injector
                self.opentime = self.props.shot_duration.sval
                self.period = self.props.mass_per_shot.sval / self.targetProps.massflow.sval
                if self.period * self.targetProps.min_injections < self.targetProps.min_duration.sval:
                    self.numInjections = int(math.ceil(self.targetProps.min_duration.sval / self.period))
                else:
                    self.numInjections = self.targetProps.min_injections
            else:
                # pulse width modulated injector
                self.period = 1. / self.props.frequency.sval
                if self.targetProps.min_injections * self.period < self.targetProps.min_duration.sval:
                    # use min_duration
                    self.numInjections = int(math.ceil(self.targetProps.min_duration.sval * self.props.frequency.sval))
                else:
                    # use min_injections *
                    self.numInjections = self.targetProps.min_injections
                self.opentime = self.targetProps.massflow.sval / self.props.full_massflow.sval * self.period

                self.props.mass_per_shot.sval = self.opentime * self.props.full_massflow.sval
            self.total_mass_injected = self.numInjections * self.props.mass_per_shot.sval
            # wet time step
            num_dt_wet = math.floor(self.opentime / TARGET_TIME_STEP_WET)
            if num_dt_wet < MIN_NUMBER_OF_TIMESTEPS_INJECTOR and TARGET_TIME_STEP_WET/2. > targetProps.quantize_raster.sval:
                num_dt_wet = math.floor(self.opentime / TARGET_TIME_STEP_WET * 2.)
            self.dt_wet = self.opentime / num_dt_wet

            # time step for initial phase
            self.initial_pause = targetProps.initial_pause.sval
            if self.initial_pause > 0:
                num_initial_dt = math.floor(self.initial_pause / 0.005)
                self.initial_dt = self.initial_pause / num_initial_dt
            else:
                num_initial_dt = 0
                self.initial_dt = 0

            self.spray_present = targetProps.spray_present.sval

            if targetProps.quantize:
                coeff = 1. / targetProps.quantize_raster.sval
                self.dt_wet = round(self.dt_wet * coeff, 0) * targetProps.quantize_raster.sval
                self.period = round(self.period * coeff, 0) * targetProps.quantize_raster.sval
                self.opentime = self.dt_wet * num_dt_wet
                self.spray_present = round(self.spray_present * coeff, 0) * targetProps.quantize_raster.sval
                self.initial_pause = round(self.initial_pause * coeff, 0) * targetProps.quantize_raster.sval

            num_dt_dry = math.floor((self.period - self.opentime - self.spray_present) / TARGET_TIME_STEP_DRY)
            self.dt_dry = self.dt_wet
            # time step for 'dry phase'
            if targetProps.extend_dt and self.period > self.opentime + self.spray_present:
#                 num_dt_dry =  math.floor((self.period - self.opentime - self.spray_present - 2*self.dt_wet) / 0.005)
                if num_dt_dry > 0:
#                    self.dt_dry = (self.period - self.opentime - self.spray_present - 2*self.dt_wet) / num_dt_dry
                    self.dt_dry = (self.period - self.opentime - self.spray_present - self.dt_wet) / num_dt_dry
                    if targetProps.quantize:
                        coeff = 1. / targetProps.quantize_raster.sval
                        self.dt_dry = round(self.dt_dry * coeff, 0) * targetProps.quantize_raster.sval
                else:
                    targetProps.extend_dt = False


            self.duration = self.numInjections * self.period
            self.closetime = self.period - self.opentime
            self.total_duration = self.duration + self.initial_pause


            self.t.append(0)
            self.m.append(0)
            # injection rate
            for i in range(self.numInjections):
                self.t.append(self.t[-1] + self.dt_wet)
                self.m.append(1)
                self.t.append(self.t[-1] + self.opentime - self.dt_wet)
                self.m.append(1)
                self.t.append(self.t[-1] + self.dt_wet)
                self.m.append(0)
                self.t.append((i + 1) * self.period)
                self.m.append(0)

            # time steps
            if(self.initial_pause > 0):
                self.t1.append(self.initial_pause)
                self.dt.append(self.initial_dt)
            if targetProps.extend_dt:
                for i in range(self.numInjections):
#                    self.t1.append(i*self.period + self.initial_pause + self.opentime + self.spray_present + 2*self.dt_wet)
                    self.t1.append(i * self.period + self.initial_pause + self.opentime + self.spray_present)
                    self.dt.append(self.dt_wet)
#                    self.t1.append(self.t1[-1]+(num_dt_dry-1)*self.dt_dry)
                    self.t1.append(self.t1[-1] + (num_dt_dry) * self.dt_dry)
                    self.dt.append(self.dt_dry)

                    if (self.period - self.opentime - self.spray_present - (self.dt_dry * num_dt_dry)) > TARGET_TIME_STEP_WET:
                        self.t1.append((i + 1) * self.period + self.initial_pause)
                        self.dt.append(self.t1[-1] - self.t1[-2])

            else:
                self.t1.append(self.duration + self.initial_pause)
                self.dt.append(self.dt_wet)

            # 3d results
            # first time step = complete
            if self.initial_pause > 0:
                self.t3.append(self.initial_pause)
                self.res.append(self.initial_pause)

            if targetProps.extend_dt:
                self.t3.append(self.initial_pause + self.opentime + self.spray_present + 2 * self.dt_wet)
                self.res.append(self.dt_wet)
                self.t3.append(self.initial_pause + self.period)
                self.res.append(self.dt_dry)
            else:
                self.t3.append(self.initial_pause + self.period)
                self.res.append(self.dt_wet)

            # intermediate injections: only every 4th time step
            for i in range(2, self.numInjections):
                if targetProps.extend_dt:
                    self.t3.append(self.t3[-1] + self.opentime + self.spray_present + 2 * self.dt_wet)
                    self.res.append(4 * self.dt_wet)
                    self.t3.append(i * self.period + self.initial_pause)
                    self.res.append(4 * self.dt_dry)
                else:
                    self.t3.append(i * self.period + self.initial_pause)
                    self.res.append(4 * self.dt_wet)
            # last injection: complete
            if targetProps.extend_dt:
                self.t3.append((self.numInjections - 1) * self.period + self.initial_pause + self.opentime + self.spray_present + 2 * self.dt_wet)
                self.res.append(self.dt_wet)
                self.t3.append(self.numInjections * self.period + self.initial_pause)
                self.res.append(self.dt_dry)
            else:
                self.t3.append(self.numInjections * self.period + self.initial_pause)
                self.res.append(self.dt_wet)

            # Backup files
            if self.initial_pause > 0:
                self.t2.append(self.initial_pause)
            for i in range(1, self.numInjections):
                self.t2.append(self.initial_pause + i * self.period)

            self.bckup.extend(self.t2)

            self.axes.plot(self.t, self.m)
            self.axes.set_ylim(0, 1.2)
            self.axes.set_xlim(0, self.total_duration)
            self.canvas.draw()

class SprayParticlesSelection(gtk.VBox):
    """Dialogue to define and visually check the particle size distribution for the SCR spray.
Particle size distribution needs to be defined within a .txt-file of plain txt format or
GIDAS format.
    """
    class SprayOverview(act.Base):
        act.namespace.defclass
        LengthAmount = act.units.amount_type('length')
        defslot('D10', LengthAmount, 0, 'length~mym')
        defslot('D30', LengthAmount, 0, 'length~mym')
        defslot('D32', LengthAmount, 0, 'length~mym')
        defslot('D43', LengthAmount, 0, 'length~mym')
        defslot('DN10', LengthAmount, 0, 'length~mym')
        defslot('DN50', LengthAmount, 0, 'length~mym')
        defslot('DN90', LengthAmount, 0, 'length~mym')
        defslot('DV10', LengthAmount, 0, 'length~mym')
        defslot('DV50', LengthAmount, 0, 'length~mym')
        defslot('DV90', LengthAmount, 0, 'length~mym')

    class SprayPropsEd(act.ui.CompositeEditor):
        def __init__(self):
            layout = act.ui.VLDesc(members=[
                act.ui.FormDesc('D10', act.ui.AmountEditor(labeltext='D10', readonly=True)),
                act.ui.FormDesc('D30', act.ui.AmountEditor(labeltext='D30', readonly=True)),
                act.ui.FormDesc('D32', act.ui.AmountEditor(labeltext='D32 (SMD)', readonly=True)),
                act.ui.FormDesc('D43', act.ui.AmountEditor(labeltext='D43', readonly=True)),
                act.ui.FormDesc('DN10', act.ui.AmountEditor(labeltext='DN10', readonly=True)),
                act.ui.FormDesc('DN50', act.ui.AmountEditor(labeltext='DN50', readonly=True)),
                act.ui.FormDesc('DN90', act.ui.AmountEditor(labeltext='DN90', readonly=True)),
                act.ui.FormDesc('DV10', act.ui.AmountEditor(labeltext='DV10', readonly=True)),
                act.ui.FormDesc('DV50', act.ui.AmountEditor(labeltext='DV50', readonly=True)),
                act.ui.FormDesc('DV90', act.ui.AmountEditor(labeltext='DV90', readonly=True)),
                        ])
            super(SprayParticlesSelection.SprayPropsEd, self).__init__(layout=layout)
            self.context = UnitContextFixed(length_unit=act.units.find('length~mym'))

    class DialogExample(gtk.Dialog):

        class NozzleStore(act.Base):
            act.namespace.defclass
            defslot('injectorName', type=str)
            defslot('diskname', type=str)

        class NozzleListEd(ui.CompositeEditor):
            def __init__(self):
                super(SprayParticlesSelection.DialogExample.NozzleListEd, self).__init__(
                        layout=ui.VLDesc([
                            ui.FormDesc('mixed', ui.ListEditor(
                                    (ui.ListColDesc(SprayParticlesSelection.DialogExample.NozzleStore.injectorName, caption='Injector Name'),
                                ), insert_row_factory=self.insert_row
                            ), directives=dict(resizex=True, resizey=True)),
                        ], directives=dict(resizex=True, resizey=True))
                )

            def insert_row(self):
                print 'insert_row clicked'
                retval = SprayParticlesSelection.DialogExample.NozzleStore()
                retval.injectorName = 'New Injector'
                retval.diskname = ''

                return retval




        def __init__(self, parent):
            gtk.Dialog.__init__(self, "My Dialog", parent, 0,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                 gtk.STOCK_OK, gtk.RESPONSE_OK))

            self.set_default_size(300, 400)

            nzlListEd = SprayParticlesSelection.DialogExample.NozzleListEd()

            self.nzlList = dm.List()

            storedNoz = spray.Storage.get_stored_nozzles()

            for nozzle in storedNoz:
                noz = SprayParticlesSelection.DialogExample.NozzleStore()
                noz.injectorName = nozzle
                noz.diskname = nozzle
                self.nzlList.append(noz)

            nzlListEd.subforms.mixed.target = self.nzlList
            ui.editor.prepare_linked(nzlListEd)

            vbox = gtk.VBox()
            label = gtk.Label("To store current setup as new nozzle, click + and enter a name")
            label.set_line_wrap(True)
            vbox.pack_start(nzlListEd.widgets.frame, fill=True, expand=True, padding=1)
            vbox.pack_start(label, fill=False, expand=False, padding=0)
            box = self.get_content_area()
            box.add(vbox)
            self.show_all()


    def __init__(self, *args, **kwargs):
        gtk.VBox.__init__(self, *args, **kwargs)
        self.sprayFileEditor = InjectorParticlePropertiesEditor()
        self.sprayFileEditor.target = InjectorProperties()
        act.ui.editor.prepare_linked(self.sprayFileEditor)
        self.props = None
        self.pack_start(self.sprayFileEditor.widgets.frame, False, False, 10)

        hbox = gtk.HBox()
        self.figure = matplotlib.pyplot.figure(facecolor='white')
        self.axes = self.figure.add_subplot(1, 1, 1)
        # self.axes.set_aspect('equal')
        self.canvas = Canvas(self.figure)
        # self.canvas.set_size_request(200,200)
        hbox.pack_start(self.canvas, expand=True, fill=True, padding=0)
        self.figure.subplots_adjust(left=0.15, bottom=0.1)

        self.sprayoverview = self.SprayOverview()
        sprayoverviewEd = self.SprayPropsEd()
        sprayoverviewEd.target = self.sprayoverview
        act.ui.editor.prepare_linked(sprayoverviewEd)
        sprayoverviewEd.widgets.frame.set_size_request(250, -1)

        vbox = gtk.VBox()
        vbox.pack_start(sprayoverviewEd.widgets.frame, expand=False, padding=0)
        button = gtk.Button('Injector Database')
        button.connect('clicked', self.store_clicked)
        vbox.pack_end(button, expand=False, padding=5)

        hbox.pack_start(vbox, expand=False, padding=0)
        self.pack_start(hbox)

    def store_clicked(self, button):
        dialog = self.DialogExample(None)
        response = dialog.run()

        if response == gtk.RESPONSE_OK:

            for noz in dialog.nzlList:
                if noz.diskname is not None and noz.diskname != noz.injectorName:
                    if noz.diskname != '':
                        noz.diskname = spray.Storage.rename_nozzle(noz.diskname, noz.injectorName)

                if (noz.diskname is None or noz.diskname == '')and noz.injectorName is not None and noz.injectorName != '':
                    noz.diskname = spray.Storage.store_nozzle(self.props, noz.injectorName)

            storedNoz = spray.Storage.get_stored_nozzles()

            for noz in dialog.nzlList:
                storedNoz.remove(noz.diskname)

            for diskname in storedNoz:
                spray.Storage.delete_nozzle(diskname)

#            name = dialog.entry.get_text()
#            if name is not None and name is not "":
#                spray.Storage.store_nozzle(self.props, name)
        elif response == gtk.RESPONSE_CANCEL:
            pass

        dialog.destroy()

    def setProperties(self, props):
        if not self.props is None:
            self.props.observers.remove(tag='GUIUPDATE')

        self.props = props
        self.sprayFileEditor.target = props
        act.ui.editor.prepare_linked(self.sprayFileEditor)
        self.axes.cla()
        self.setAxesProps()

        if self.props is not None:
            self.props.observe('particlesize_fname', self.fname_changed, tag='GUIUPDATE')
            if self.props.adjunct.get('diameters', None) is not None:
                d = self.props.adjunct.get('diameters', None)
                p = self.props.adjunct.get('probabilities', None)
                self.set_diagram(d, p)

    def setLastdir(self, lastdir):
        self.sprayFileEditor.prefs.lastdir = lastdir

    def setAxesProps(self):
        self.axes.set_axis_bgcolor('white')
        self.axes.set_xlabel('D [micron]')
        self.axes.set_ylabel('Probability density [-]')
        self.figure.subplots_adjust(left=0.15, bottom=0.1)

    def fname_changed(self, ev=None, obj=None):
#         print 'fname_changed'
        self.axes.cla()
        self.setAxesProps()
        d = []
        p = []
        if not ev is None:
            try:
#                 print ev
                fname = self.props.particlesize_fname
                d, p = spray.loadParticlesSizes(fname)
                if(self.props.adjunct.get('diameters', None)) is not None:
                    self.props.adjunct.remove('diameters')
                self.props.adjunct.add('diameters', d)
                if(self.props.adjunct.get('probabilities', None)) is not None:
                    self.props.adjunct.remove('probabilities')
                self.props.adjunct.add('probabilities', p)
                self.set_diagram(d, p)
            except IOError:
                print 'Could not access/ read the file specified'
                return False
            except ValueError:
                print 'Could not read', fname, '! Possibly wrong format?'
                return False
        return True


    def set_diagram(self, d, p):
        self.axes.plot(d, p)
        self.canvas.draw()
        self.d = d
        self.p = p
        sprayData = spray.Distribution(d, p)
        self.sprayoverview.D10.value = round(sprayData.getD10(), 2)
        self.sprayoverview.D30.value = round(sprayData.getD30(), 2)
        self.sprayoverview.D32.value = round(sprayData.getD32(), 2)
        self.sprayoverview.D43.value = round(sprayData.getD43(), 2)
        self.sprayoverview.DN10.value = round(sprayData.getDN10(), 2)
        self.sprayoverview.DN50.value = round(sprayData.getDN50(), 2)
        self.sprayoverview.DN90.value = round(sprayData.getDN90(), 2)
        self.sprayoverview.DV10.value = round(sprayData.getDV10(), 2)
        self.sprayoverview.DV50.value = round(sprayData.getDV50(), 2)
        self.sprayoverview.DV90.value = round(sprayData.getDV90(), 2)
