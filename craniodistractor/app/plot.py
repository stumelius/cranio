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

from pyqtgraph.Qt import QtGui, QtCore
from craniodistractor.app import app

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

color_palette = [(76, 114, 176), (85, 168, 104), (196, 78, 82), 
                 (129, 114, 178), (204, 185, 116), (100, 181, 205)]

class PlotWindow(QtGui.QDialog):
    
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout()
        self.plot_widget = pg.PlotWidget()
        self.ok_button = QtGui.QPushButton('OK')
        self.region_items = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Plot')
        self.resize(800,800)
        self.setLayout(self.layout)
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.ok_button_clicked)
    
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
        w = pg.LinearRegionItem(initial_values, bounds=bounds, movable=movable, brush=pg.mkBrush(*color))
        self.plot_widget.addItem(w)
        self.region_items.append(w)
        
    @QtCore.pyqtSlot()
    def ok_button_clicked(self):
        print('OK clicked')

if __name__ == '__main__':
    x = list(range(100))
    y = [random.gauss(0,1) for _ in range(len(x))]
    w = PlotWindow()
    w.plot(x, y, pen=pg.mkPen(100,100,100))
    for _ in range(2):
        w.add_region([1, 30])
    sys.exit(w.exec_())
    #pyqtgraph.examples.run()