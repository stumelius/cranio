'''
This module implements the graphical user interface elements of the craniodistractor application.

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
from PyQt4 import QtGui

from cranio.app.plot import PlotWidget, PlotWindow

class MeasurementDialog(PlotWindow):
    
    def __init__(self):
        self.distractor_groupbox = QtGui.QGroupBox()
        self.distractor_groupbox_layout = QtGui.QVBoxLayout()
        self.distractor_edit = QtGui.QSpinBox()
        super(MeasurementDialog, self).__init__()
        self.plot_widget = PlotWidget()
        self.add_plot(self.plot_widget)
        
    def init_ui(self):
        super(MeasurementDialog, self).init_ui()
        self.setWindowTitle('Measurement dialog')
        self.distractor_groupbox_layout.addWidget(self.distractor_edit)
        self.distractor_groupbox.setLayout(self.distractor_groupbox_layout)
        self.layout.insertWidget(0, self.distractor_groupbox)
        self.distractor_groupbox.setTitle('Distractor index')
    
    @property  
    def distractor_index(self):
        return self.distractor_edit.value()
    
    @distractor_index.setter
    def distractor_index(self, value):
        if not isinstance(value, int):
            raise ValueError('Distractor index must be an integer')
        self.distractor_edit.setValue(value)