'''
MODULE DESCRIPTION

Copyright (C) 2017  Simo Tumelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import random
import sys

import pyqtgraph as pg
import pyqtgraph.examples

from functools import partial
from pyqtgraph.Qt import QtGui, QtCore
from craniodistractor.app import app

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

color_palette = [(76, 114, 176), (85, 168, 104), (196, 78, 82), 
                 (129, 114, 178), (204, 185, 116), (100, 181, 205)]

class RegionEditWidget(QtGui.QGroupBox):
    
    def __init__(self, region, name=None, parent=None):
        super(RegionEditWidget, self).__init__(name, parent)
        self.region = region
        self.main_layout = QtGui.QHBoxLayout()
        self.minimum_edit = QtGui.QDoubleSpinBox()
        self.maximum_edit = QtGui.QDoubleSpinBox()
        self.init_ui()
        
    def init_ui(self):
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.minimum_edit)
        self.main_layout.addWidget(self.maximum_edit)
        self.minimum_edit.setSingleStep(0.01)
        self.maximum_edit.setSingleStep(0.01)
        # FIXME: region.bounds is always (0,0)
        #self.minimum_edit.setRange(self.region.bounds.left(), self.region.bounds.right())
        self.minimum_edit.setValue(self.region.getRegion()[0])
        self.maximum_edit.setValue(self.region.getRegion()[1])
        
        # connect signals
        self.minimum_edit.valueChanged.connect(partial(self.value_changed, self.minimum_edit))
        self.maximum_edit.valueChanged.connect(partial(self.value_changed, self.maximum_edit))
        
        self.region.sigRegionChanged.connect(self.region_changed)
        
    @QtCore.pyqtSlot(object, float)
    def value_changed(self, widget, value):
        old_edges = self.region.getRegion()
        if widget == self.minimum_edit:
            new_edges = (max(old_edges), value)
        elif widget == self.maximum_edit:
            new_edges = (value, min(old_edges))
        else:
            ValueError('Invalid widget')
        self.region.setRegion(new_edges)
        
    @QtCore.pyqtSlot()
    def region_changed(self):
        new_edges = self.region.getRegion()
        self.minimum_edit.setValue(min(new_edges))
        self.maximum_edit.setValue(max(new_edges))

class RegionWidget(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(RegionWidget, self).__init__(parent)
        self.main_layout = QtGui.QHBoxLayout()
        self.plot_widget = pg.PlotWidget()
        self.edit_layout = QtGui.QVBoxLayout()
        self.region_items = []
        self.add_button = QtGui.QPushButton('Add')
        self.init_ui()
        
    def init_ui(self):
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addLayout(self.edit_layout)
        self.edit_layout.addWidget(self.add_button)
        self.add_button.clicked.connect(self.add_button_clicked)
        
    def x(self):
        try:
            return self.plot_widget.plotItem.dataItems[0].xData
        except IndexError:
            return None
    
    def y(self):
        try:
            return self.plot_widget.plotItem.dataItems[0].xData
        except IndexError:
            return None
    
    def plot(self, *args, **kwargs):
        self.plot_widget.plot(*args, **kwargs)
        
    def add_region(self, initial_values, bounds=None, movable=True):
        if bounds is None:
            bounds = [min(self.x()), max(self.x())]
        alpha = 125
        color = list(color_palette[len(self.region_items)]) + [alpha]
        item = pg.LinearRegionItem(initial_values, bounds=bounds, movable=movable, brush=pg.mkBrush(*color))
        self.plot_widget.addItem(item)
        self.edit_layout.insertWidget(self.edit_layout.count()-1, RegionEditWidget(item))
        self.region_items.append(item)
        
    @QtCore.pyqtSlot()
    def add_button_clicked(self):
        self.add_region([min(self.x()), max(self.x())/2])

class PlotWindow(QtGui.QDialog):
    
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout()
        self.region_widget = RegionWidget()
        self.ok_button = QtGui.QPushButton('OK')
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Plot')
        self.resize(800,800)
        self.setLayout(self.layout)
        self.layout.addWidget(self.region_widget)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        
    @QtCore.pyqtSlot()
    def ok_button_clicked(self):
        print('OK clicked')

if __name__ == '__main__':
    x = list(range(100))
    y = [random.gauss(0,1) for _ in range(len(x))]
    w = PlotWindow()
    w.region_widget.plot(x, y, pen=pg.mkPen(100,100,100))
    for _ in range(2):
        w.region_widget.add_region([1, 30])
    sys.exit(w.exec_())
    #pyqtgraph.examples.run()