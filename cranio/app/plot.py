'''
This module implements classes and functions for data visualization and computer-aided event detection.

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
import datetime
import logging
import numpy as np
import pandas as pd
import pyqtgraph as pg

from functools import partial, lru_cache
from pyqtgraph.Qt import QtGui, QtCore
from cranio.producer import datetime_to_seconds
from cranio.core import Packet

# pyqtgraph style settings
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# custom color palette for plots
color_palette = [(76, 114, 176), (85, 168, 104), (196, 78, 82), 
                 (129, 114, 178), (204, 185, 116), (100, 181, 205)]

# default plot configuration
plot_configuration = {'antialias': True, 'pen': pg.mkPen(color_palette[0])}

def remove_widget_from_layout(layout, widget):
    '''
    Removes a widget from a layout (calls widget.deleteLater()).
    
    Args:
        - layout: a PyQt Layout object
        - widget: a PyQt Widget object
        
    Returns:
        None
        
    Raises:
        None
    '''
    layout.removeWidget(widget)
    widget.deleteLater()
    
def set_data(data_item, x, y):
    '''
    Sets data on a PlotDataItem. Also applies default plot configuration (see plot_configuration).
    
    Args:
        - data_item: a PlotDataItem object
        - x: x values
        - y: y values
        
    Returns:
        None
        
    Raises:
        None
    '''
    data_item.setData(x, y, **plot_configuration)

def x_filter(func, data_item):
    '''
    Filters a PlotDataItem based on its X values and updates the PlotDataItem data
    
    Args:
        - func: a function
        - data_item: a PlotDataItem object
        
    Returns:
        None
        
    Raises:
        None
    '''
    I = np.where(func(data_item.xData))[0]
    set_data(data_item, data_item.xData[I], data_item.yData[I])

# filters n most previous seconds
time_filter = lambda n_seconds, data_item: x_filter(lambda x: x > (x[-1] - n_seconds), data_item)

def update_plot(plot_widget, x, y):
    '''
    Adds given x and y values to a plot.
    
    Args:
        - x: x values to be added
        - y: y values to be added
    
    Returns:
        A pg.PlotDataItem object

    Raises:
        None
    '''
    data_items = plot_widget.getPlotItem().dataItems 
    if len(data_items) > 1:
        raise NotImplementedError('Too many data items in plot')
    elif len(data_items) == 0:
        plot_widget.plot()
        logging.info('No plot to update, creating an empty plot')
    data_item = data_items[0]
    old_x = data_item.xData
    old_y = data_item.yData
    if old_x is None:
        old_x = np.array([])
    new_x = np.append(old_x, x)
    if old_y is None:
        old_y = np.array([])
    new_y = np.append(old_y, y)
    set_data(data_item, new_x, new_y)
    return data_item

class PlotBase(QtGui.QWidget):
    ''' Base class for plot widgets '''
    
    def __init__(self, parent=None):
        super(PlotBase, self).__init__(parent)
        self.plot_widget = pg.PlotWidget()
        
    def __getattr__(self, attr):
        ''' Object composition from self.plot_widget (PlotWidget) '''
        if attr in {'__getstate__', '__setstate__'}:
            return object.__getattr__(self, attr)
        return getattr(self.plot_widget, attr)
    
    @property
    def x_label(self):
        return self.getAxis('bottom').labelText
    
    @x_label.setter
    def x_label(self, value):
        self.setLabel('bottom', value)
        
    @property
    def y_label(self):
        return self.getAxis('left').labelText
    
    @y_label.setter
    def y_label(self, value):
        self.setLabel('left', value)
    
    def plot(self, x, y):
        ''' Calls the plot_widget.plot method with x and y input parameters '''
        self.plot_widget.plot(list(x), list(y), **plot_configuration)
        
    def x(self):
        ''' Returns x values from the plot '''
        try:
            return self.plot_widget.getPlotItem().dataItems[0].xData
        except IndexError:
            return None
    
    def y(self):
        ''' Returns y values from the plot '''
        try:
            return self.plot_widget.getPlotItem().dataItems[0].xData
        except IndexError:
            return None

class RegionWidget(PlotBase):
    ''' Widget for creating plots with selectable regions '''
    
    def __init__(self, parent=None):
        super(RegionWidget, self).__init__(parent)
        self.main_layout = QtGui.QHBoxLayout()
        self.edit_layout = QtGui.QVBoxLayout()
        # region items mapped as {LinearRegionItem: RegionEditWidget}
        self.region_edit_map = {}
        self.add_button = QtGui.QPushButton('Add')
        self.init_ui()
        
    def init_ui(self):
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addLayout(self.edit_layout)
        self.edit_layout.addWidget(self.add_button)
        self.add_button.clicked.connect(self.add_button_clicked)
        
    def find_region_by_edit(self, edit_widget):
        ''' Finds a LinearRegionItem paired to a RegionEditWidget '''
        try:
            return [key for key, value in self.region_edit_map.items() if value == edit_widget][0]
        except IndexError:
            raise ValueError('No matching edit widget found')
        
    def add_region(self, initial_values, bounds=None, movable=True):
        '''
        Adds a region to the plot and returns a RegionEditWidget.
        
        Args:
            - initial_values: initial region edges
            - bounds: region bounds
            - movable: boolean
            
        Returns:
            A RegionEditWidget
            
        Raises:
            None
        '''
        if bounds is None:
            bounds = [min(self.x()), max(self.x())]
        alpha = 125
        color = list(color_palette[len(self.region_edit_map)]) + [alpha]
        item = pg.LinearRegionItem(initial_values, bounds=bounds, movable=movable, brush=pg.mkBrush(*color))
        self.plot_widget.addItem(item)
        edit_widget = RegionEditWidget(item)
        edit_widget.remove_button.clicked.connect(partial(self.remove_region, edit_widget))
        self.edit_layout.insertWidget(self.edit_layout.count()-1, edit_widget)
        self.region_edit_map[item] = edit_widget
        return edit_widget
    
    def remove_region(self, edit_widget):
        '''
        Removes a region from the plot.
        
        Args:
            - edit_widget: a RegionEditWidget object
            
        Returns:
            None
            
        Raises:
            None
        '''
        key = self.find_region_by_edit(edit_widget)
        self.region_edit_map.pop(key, None)
        self.plot_widget.removeItem(key)
        remove_widget_from_layout(self.edit_layout, edit_widget)
        
    @QtCore.pyqtSlot()
    def add_button_clicked(self):
        '''
        Adds a region to the widget. The region covers the first half of the used x-axis.
        Called when add button is clicked.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        self.add_region([min(self.x()), max(self.x())/2])
        
class RegionEditWidget(QtGui.QGroupBox):
    ''' Widget for editing a LinearRegionItem '''
    
    def __init__(self, parent: pg.LinearRegionItem, name=None):
        super(RegionEditWidget, self).__init__()
        self.parent = parent
        self.main_layout = QtGui.QVBoxLayout()
        self.name_layout = QtGui.QHBoxLayout()
        self.boundary_layout = QtGui.QHBoxLayout()
        self.name_label = QtGui.QLabel('Identifier')
        self.name_edit = QtGui.QLineEdit()
        self.name = name
        self.minimum_edit = QtGui.QDoubleSpinBox()
        self.maximum_edit = QtGui.QDoubleSpinBox()
        self.remove_button = QtGui.QPushButton('Remove')
        self.init_ui()
        
    def init_ui(self):
        self.setTitle('Region')
        self.setLayout(self.main_layout)
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_edit)
        self.main_layout.addLayout(self.name_layout)
        self.main_layout.addLayout(self.boundary_layout)
        self.boundary_layout.addWidget(self.minimum_edit)
        self.boundary_layout.addWidget(self.maximum_edit)
        self.main_layout.addWidget(self.remove_button)
        self.minimum_edit.setSingleStep(0.01)
        self.maximum_edit.setSingleStep(0.01)
        # FIXME: region.bounds is always (0,0)
        #self.minimum_edit.setRange(self.region.bounds.left(), self.region.bounds.right())
        self.minimum_edit.setValue(self.region()[0])
        self.maximum_edit.setValue(self.region()[1])
        
        # connect signals
        self.minimum_edit.valueChanged.connect(partial(self.value_changed, self.minimum_edit))
        self.maximum_edit.valueChanged.connect(partial(self.value_changed, self.maximum_edit))
        self.parent.sigRegionChanged.connect(self.region_changed)
        # responsibility for connecting the remove button lies in the RegionWidget
        
    @property
    def name(self):
        return self.name_edit.text()
    
    @name.setter
    def name(self, value):
        self.name_edit.setText(value)
        
    def region(self):
        ''' Returns region as a tuple '''
        return self.parent.getRegion()
    
    def bounds(self):
        ''' Returns bounds as a tuple '''
        raise NotImplementedError
        return (self.parent.bounds.left(), self.parent.bounds.right())
    
    def set_region(self, edges):
        ''' Sets new region edges '''
        self.parent.setRegion(edges)
        
    def set_bounds(self, bounds):
        ''' Set new region bounds '''
        self.parent.setBounds(bounds)
        
    @QtCore.pyqtSlot(object, float)
    def value_changed(self, widget: QtGui.QDoubleSpinBox, value: float):
        '''
        Update region edges. 
        Called when a region edit widgets are manipulated.
        
        Args:
            - widget: RegionWidget object
            - value: changed edge value
            
        Returns:
            None
            
        Raises:
            ValueError: Invalid widget
        '''
        old_edges = self.region()
        if widget == self.minimum_edit:
            new_edges = (max(old_edges), value)
        elif widget == self.maximum_edit:
            new_edges = (value, min(old_edges))
        else:
            ValueError('Invalid widget')
        self.set_region(new_edges)
        
    @QtCore.pyqtSlot()
    def region_changed(self):
        '''
        Update region edges to minimum and maximum edit widgets.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        new_edges = self.region()
        self.minimum_edit.setValue(min(new_edges))
        self.maximum_edit.setValue(max(new_edges))
        
class PlotWidget(PlotBase):
    
    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    
    def __init__(self):
        super(PlotWidget, self).__init__()
        self.layout = QtGui.QHBoxLayout()
        self.button_layout = QtGui.QVBoxLayout()
        self.start_button = QtGui.QPushButton('Start')
        self.stop_button = QtGui.QPushButton('Stop')
        
        self.update_timer = QtCore.QTimer()
        self.start_time = None
        self.display_seconds = 5
        
        self.producer_process = None
        self.data = []
        
        self.init_ui()
        
    def init_ui(self):
        self.setLayout(self.layout)
        self.layout.addWidget(self.plot_widget)
        self.layout.addLayout(self.button_layout)
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.stop_button)
        
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.update_timer.timeout.connect(self.update)
    
    def update(self):
        '''
        Reads data from a producer and appends that to the plot.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        #df = self.producer_process.read()
        #if len(df) > 0:
        #    self.data.append(df)
        packets = self.producer_process.get_all()
        if len(packets) > 0:
            packet = Packet.concat(packets)
            self.data.append(packet)
            # FIXME: get producer info instead of using static 'torque (Nm)'
            self.append(datetime_to_seconds(packet.index, self.start_time), packet.data['torque (Nm)'])

    def append(self, x, y):
        '''
        Appends data to the plot.
        
        Args:
            - x: list of x values to append
            - y: list of y values to append
            
        Returns:
            None
            
        Raises:
            None
        '''
        time_filter(self.display_seconds, update_plot(self.plot_widget, x, y))
        
    def is_active(self) -> bool:
        '''
        Returns a boolean indicating if the real-time plotting is on-going
        
        Args:
            None
            
        Returns:
            Boolean
            
        Raises:
            None
        '''
        return self.start_event.is_set()

    def start_button_clicked(self):
        '''
        Starts the producer process if is not None. Otherwise, nothing happens.
        Parent widget Ok button is disabled. Emits signal: started.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        if self.producer_process is None:
            return
        if self.start_time is None:
            self.start_time = datetime.datetime.utcnow()
        self.update_timer.start(0)
        self.producer_process.start()
        self.started.emit()
        self.parent().ok_button.setEnabled(False)
        
    def stop_button_clicked(self):
        '''
        Stop the producer process if is not None. Otherwise, nothing happens.
        Parent widget Ok button is enabled. Emits signal: stopped.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        if self.producer_process is None:
            return
        self.producer_process.pause()
        self.update_timer.stop()
        self.stopped.emit()
        self.parent().ok_button.setEnabled(True)

class PlotWindow(QtGui.QDialog):
    ''' A window for plot widgets '''
    
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout()
        self.plot_widgets = []
        self.ok_button = QtGui.QPushButton('Ok')
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Plot')
        self.resize(800,800)
        self.setLayout(self.layout)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        
    def __contains__(self, key):
        ''' Implements in operator '''
        return key in self.plot_widgets
    
    def __getitem__(self, key):
        ''' Implements [] accessor '''
        return self.plot_widgets[key]
        
    def add_plot(self, widget):
        ''' Adds a plot widget to the window '''
        widget.setMenuEnabled(False)
        self.plot_widgets.append(widget)
        self.layout.insertWidget(self.layout.count()-1, widget)
        return widget
    
    def get_plot(self, index=0):
        ''' Alternative for plot_window[index] '''
        return self[index]
    
    def remove_plot(self, widget):
        ''' Removes a plot widget from the window '''
        self.plot_widgets.remove(widget)
        remove_widget_from_layout(self.layout, widget)
        
    @QtCore.pyqtSlot()
    def ok_button_clicked(self):
        '''
        Create and show a modal RegionWindow containing the plotted data.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        plot_widget = self.get_plot()
        data = pd.concat([p.as_dataframe() for p in plot_widget.data])
        data.index = datetime_to_seconds(data.index, plot_widget.start_time)
        window = RegionWindow(self)
        region_widget = RegionWidget()
        window.add_plot(region_widget)
        region_widget.plot(data.index.values, data[plot_widget.y_label].tolist())
        window.exec_()
        
class RegionWindow(PlotWindow):
    @QtCore.pyqtSlot()
    def ok_button_clicked(self):
        ''' Closes the window '''
        QtGui.QMessageBox.information(self, 'Success', 'Nothing to see here, come back later!')
        self.close()
        