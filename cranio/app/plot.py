import logging
import pyqtgraph as pg
import pandas as pd
from typing import Tuple
from functools import partial
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QLayout, QWidget, QWidgetItem, QSpacerItem,
                             QDialog, QLabel, QVBoxLayout, QPushButton,
                             QHBoxLayout, QDoubleSpinBox, QLineEdit,
                             QGroupBox, QMessageBox, QSpinBox, QGridLayout,
                             QCheckBox)
from cranio.database import AnnotatedEvent, DISTRACTION_EVENT_TYPE_OBJECT, Document
# pyqtgraph style settings
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# custom color palette for plots
color_palette = [(76, 114, 176), (85, 168, 104), (196, 78, 82), 
                 (129, 114, 178), (204, 185, 116), (100, 181, 205)]


def remove_widget_from_layout(layout: QLayout, widget: QWidget):
    '''
    Removes a widget from a layout (calls widget.deleteLater()).
    
    Args:
        - layout: QtGui.QLayout object
        - widget: QtGui.QWidget object
        
    Returns:
        None
        
    Raises:
        None
    '''
    layout.removeWidget(widget)
    widget.deleteLater()


def clear_layout(layout: QLayout):
    ''' Clears a QLayout object  '''
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)

        if isinstance(item, QWidgetItem):
            item.widget().close()
        elif isinstance(item, QSpacerItem):
            pass
        else:
            clear_layout(item.layout())

        # remove the item from layout
        layout.removeItem(item)


class PlotWidget(pg.PlotWidget):
    ''' Widget for displaying (real-time) plots '''
    
    # custom color palette
    color_palette = [(76, 114, 176), (85, 168, 104), (196, 78, 82), 
                     (129, 114, 178), (204, 185, 116), (100, 181, 205)]
    
    # default plot configuration
    plot_configuration = {'antialias': True, 'pen': pg.mkPen(color_palette[0])}
    
    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.x = []
        self.y = []
        self.init_ui()
        
    def init_ui(self):
        self.showGrid(True, True, 0.1)
        self.enable_interaction(False)
    
    @property
    def x_label(self):
        return self.getAxis('bottom').labelText
    
    @x_label.setter
    def x_label(self, value):
        if value is None:
            value = ''
        self.setLabel('bottom', value)
        
    @property
    def y_label(self):
        return self.getAxis('left').labelText
    
    @y_label.setter
    def y_label(self, value):
        if value is None:
            value = ''
        self.setLabel('left', value)
        
    def enable_interaction(self, bool_: bool):
        self.setMouseEnabled(bool_, bool_)
        self.setMenuEnabled(bool_)
        
    def clear_plot(self):
        ''' Clear the plot and stored x and y values '''
        self.x = []
        self.y = []
        return self.getPlotItem().clear()
    
    def plot(self, x, y, mode='o'):
        ''' Calls the plot_widget.plot method with x and y input parameters '''
        if mode == 'o':
            self.x = list(x)
            self.y = list(y)
        elif mode == 'a':
            self.x += list(x)
            self.y += list(y)
        else:
            raise ValueError('Invalid mode {}'.format(mode))
        self.getPlotItem().plot(self.x, self.y, clear=True, **self.plot_configuration)
        return self


class RegionEditWidget(QGroupBox):
    ''' Widget for editing a LinearRegionItem '''
    
    def __init__(self, parent: pg.LinearRegionItem, event_number: int):
        super(RegionEditWidget, self).__init__()
        self.parent = parent
        self.event_number = event_number
        # layouts
        self.main_layout = QVBoxLayout()
        self.done_layout = QHBoxLayout()
        self.boundary_layout = QHBoxLayout()
        # widgets
        self.done_label = QLabel('Done')
        self.done_checkbox = QCheckBox()
        self.minimum_edit = QDoubleSpinBox()
        self.maximum_edit = QDoubleSpinBox()
        self.remove_button = QPushButton('Remove')
        self.init_ui()
        
    def init_ui(self):
        self.setTitle('Region')
        self.setLayout(self.main_layout)
        self.done_layout.addWidget(self.done_label)
        self.done_layout.addWidget(self.done_checkbox)
        self.boundary_layout.addWidget(self.minimum_edit)
        self.boundary_layout.addWidget(self.maximum_edit)
        self.main_layout.addLayout(self.done_layout)
        self.main_layout.addLayout(self.boundary_layout)
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

    def is_done(self) -> bool:
        """
        Return boolean indicating if the done checkbox state is Checked.

        :return:
        """
        return self.done_checkbox.checkState() == QtCore.Qt.Checked

    def set_done(self, state: bool):
        """
        Set done check box state as Checked (True) or Unchecked (False).

        :param state:
        :return:
        """
        state_map = {True: QtCore.Qt.Checked, False: QtCore.Qt.Unchecked}
        self.done_checkbox.setCheckState(state_map[state])

    def left_edge(self) -> float:
        """
        Return left edge of the region.

        :return:
        """
        return self.region()[0]

    def right_edge(self) -> float:
        """
        Return right edge of the region.

        :return:
        """
        return self.region()[1]

    def get_annotated_event(self) -> AnnotatedEvent:
        """
        Create an AnnotatedEvent table row from the edit widget data.

        :return:
        """
        # only distraction events are supported
        return AnnotatedEvent(event_type=DISTRACTION_EVENT_TYPE_OBJECT.event_type,
                              event_num=self.event_number, document_id=Document.get_instance(),
                              event_begin=self.left_edge(), event_end=self.right_edge(), annotation_done=self.is_done())
        
    def region(self):
        ''' Returns region as a tuple '''
        return self.parent.getRegion()
    
    def bounds(self):
        ''' Returns bounds as a tuple '''
        # return self.parent.bounds.left(), self.parent.bounds.right()
        raise NotImplementedError
    
    def set_region(self, edges):
        ''' Sets new region edges '''
        self.parent.setRegion(edges)
        
    def set_bounds(self, bounds):
        ''' Set new region bounds '''
        self.parent.setBounds(bounds)

    def value_changed(self, widget: QDoubleSpinBox, value: float):
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


class RegionPlotWidget(QWidget):
    ''' Widget for creating plots with selectable regions '''
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_widget = PlotWidget()
        self.main_layout = QHBoxLayout()
        self.edit_layout = QVBoxLayout()
        self.add_layout = QGridLayout()
        # region items mapped as {LinearRegionItem: RegionEditWidget}
        self.region_edit_map = dict()
        self.add_count = QSpinBox()
        self.add_button = QPushButton('Add')
        self.remove_all_button = QPushButton('Remove all')
        self.init_ui()
        
    def init_ui(self):
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addLayout(self.edit_layout)
        self.add_layout.addWidget(self.add_count, 0, 0)
        self.add_layout.addWidget(self.add_button, 0, 1)
        self.add_layout.addWidget(self.remove_all_button, 1, 0, 1, 2)
        self.edit_layout.addLayout(self.add_layout)
        self.add_button.clicked.connect(self.add_button_clicked)
        self.remove_all_button.clicked.connect(self.remove_all)
        
    def __getattr__(self, attr):
        ''' Object composition from self.plot_widget (PlotWidget) '''
        if attr in {'__getstate__', '__setstate__'}:
            return object.__getattr__(self, attr)
        return getattr(self.plot_widget, attr)
    
    @property
    def x(self):
        return self.plot_widget.x
    
    @property
    def y(self):
        return self.plot_widget.y

    def region_count(self) -> int:
        """
        Return number of regions.

        :return:
        """
        return len(self.region_edit_map)

    def set_add_count(self, value: int):
        """
        Set integer value to the add count widget.

        :param value:
        :return:
        """
        self.add_count.setValue(value)

    def get_region_edit(self, index: int) -> RegionEditWidget:
        """
        Return region edit widget for region at specified index.

        :param index:
        :return:
        """
        # note: edit widgets are stored in a dict and therefore are in no specific order
        return list(self.region_edit_map.values())[index]
        
    def find_region_by_edit(self, edit_widget: RegionEditWidget) -> pg.LinearRegionItem:
        ''' Finds a LinearRegionItem paired to a RegionEditWidget '''
        try:
            return [key for key, value in self.region_edit_map.items() if value == edit_widget][0]
        except IndexError:
            raise ValueError('No matching edit widget found')
        
    def add_region(self, edges: Tuple[float, float], bounds: Tuple[float, float]=None,
                   movable: bool=True) -> RegionEditWidget:
        """
        Add a region to the plot.

        :param edges: Region edges
        :param bounds: Region bounds
        :param movable:
        :return:
        """
        if bounds is None:
            bounds = [min(self.x), max(self.x)]
        alpha = 125
        color = list(color_palette[len(self.region_edit_map)]) + [alpha]
        item = pg.LinearRegionItem(edges, bounds=bounds, movable=movable, brush=pg.mkBrush(*color))
        self.plot_widget.addItem(item)
        # event numbering by insertion order
        edit_widget = RegionEditWidget(item, event_number=self.region_count()+1)
        edit_widget.remove_button.clicked.connect(partial(self.remove_region, edit_widget))
        self.edit_layout.insertWidget(self.edit_layout.count()-1, edit_widget)
        self.region_edit_map[item] = edit_widget
        return edit_widget
    
    def remove_region(self, edit_widget: RegionEditWidget):
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

    def remove_at(self, index: int) -> RegionEditWidget:
        """
        Remove region at specified index.

        :param index:
        :return: RegionEditWidget of the removed region
        """
        edit_widget = self.get_region_edit(index)
        self.remove_region(edit_widget)
        return edit_widget

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
        if len(self.x) == 0:
            # Exceptions in a PyQt slot will result in qFatal() and crash the app
            # Therefore, error is logged
            # More info here: https://stackoverflow.com/questions/43641638/unhandled-exceptions-in-pyqt5
            logging.error('Unable to add region to empty plot')
            return 0
        count = self.add_count.value()
        if count > 0:
            x_min = min(self.x)
            interval = (max(self.x) - x_min) / count
            for i in range(count):
                # insert at uniform intervals
                low = x_min + i*interval
                high = x_min + (i+1)*interval
                self.add_region([low, high])

    def remove_all(self):
        ''' Remove all regions from the widget '''
        for edit_widget in list(self.region_edit_map.values()):
            self.remove_region(edit_widget)


class VMultiPlotWidget(QWidget):
    '''
    A multi-plot dialog. Plots organized vertically as separate widgets.
    '''
    
    def __init__(self, parent=None):
        super(VMultiPlotWidget, self).__init__(parent=parent)
        self.plot_widgets = []
        self.title_label = QLabel()
        self.main_layout = QVBoxLayout()
        self.init_ui()
        # add placeholder widget
        self.placeholder = PlotWidget()
        self.main_layout.addWidget(self.placeholder)

    def init_ui(self):
        self.setLayout(self.main_layout)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.main_layout.addWidget(self.title_label)
        
    @property
    def title(self):
        return self.title_label.text()
    
    @title.setter
    def title(self, value):
        self.title_label.setText(value)
    
    def find_plot_widget_by_label(self, label: str):
        ''' Finds a plot widget by its label (i.e., y axis name) '''
        for p in self.plot_widgets:
            if p.y_label == label:
                return p
    
    def add_plot_widget(self, label: str):
        ''' Adds a plot widget by a label (i.e., y axis name) '''
        if self.find_plot_widget_by_label(label) is not None:
            raise ValueError('A plot widget with label {} already exists'.format(label))
        # if placeholder exists, use it
        # NOTE: no need to add to layout as placeholder is there by default
        if self.placeholder is not None:
            plot_widget = self.placeholder
            self.placeholder = None
        # if no placeholder exists, create new
        else:
            plot_widget = PlotWidget()
            self.main_layout.addWidget(plot_widget)
        plot_widget.y_label = label
        self.plot_widgets.append(plot_widget)
        return plot_widget

    def plot(self, data, title='', mode='o'):
        '''
        Plots the input pandas.DataFrame into a figure grid.
        
        Args:
            - data: pandas.DataFrame where index is the x column
            - title: plot title, string ('' by default)
            - mode: 'o' (overwrite) or 'a' (append)
        
        Returns:
            None
            
        Raises:
            ValueError: Invalid mode
        '''
        # Data is stored as a DataFrame
        # The dataframe is appended during recording
        # Ideally, the real-time plot is updated automatically once the dataframe is updated
        # Alternatively, real-time plot can be updated at regular intervals
        # 
        # Example:
        # update_timer = QTimer()
        # update_timer.setInterval(100)
        # update_timer.timeout.connect(self.update)
        # def update(self):
        #     data = devices.output()
        #     self.figure_window.update(data)
        
        
        self.title = title
        # find already initialized columns
        initialized_columns = [p.y_label for p in self.plot_widgets if p.y_label in data]
        # leftover columns need to be initialized
        non_initialized_columns = filter(lambda c: c not in initialized_columns, data.columns)
        for c in non_initialized_columns:
            self.add_plot_widget(c)
        
        # plot each column
        for c in data:
            plot_widget = self.find_plot_widget_by_label(c)
            plot_widget.plot(x=data.index, y=data[c], mode=mode)
    
    def clear(self):
        ''' Clears all plot widgets '''
        for p in self.plot_widgets:
            p.clear()
            
    def reset(self):
        ''' Removes all plot widgets from the window '''
        for p in self.plot_widgets:
            remove_widget_from_layout(self.main_layout, p)
        self.plot_widgets = []


class PlotWindow(QDialog):
    ''' A window for plot widgets '''
    
    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    
    def __init__(self, producer_process=None, parent=None):
        super(PlotWindow, self).__init__(parent)
        self.producer_process = producer_process
        self.main_layout = QVBoxLayout()
        self.plot_layout = QHBoxLayout()
        self.start_stop_layout = QVBoxLayout()
        self.multiplot_widget = VMultiPlotWidget()
        self.ok_button = QPushButton('Ok')
        self.start_button = QPushButton('Start')
        self.stop_button = QPushButton('Stop')
        self.update_timer = QtCore.QTimer()
        self.update_interval = 0.05 # seconds
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Plot window')
        self.resize(800,800)
        self.plot_layout.addWidget(self.multiplot_widget)
        self.plot_layout.addLayout(self.start_stop_layout)
        self.start_stop_layout.addWidget(self.start_button)
        self.start_stop_layout.addWidget(self.stop_button)
        self.main_layout.addLayout(self.plot_layout)
        self.main_layout.addWidget(self.ok_button)
        self.setLayout(self.main_layout)
        # connect signals
        self.ok_button.clicked.connect(self.ok_button_clicked)
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.update_timer.timeout.connect(self.update)
        
    def plot(self, df: pd.DataFrame):
        self.multiplot_widget.plot(df)
        
    def add_plot(self, label: str):
        ''' Adds a plot widget to the window '''
        return self.multiplot_widget.add_plot_widget(label)
    
    def get_plot(self, label: str):
        ''' Alternative for plot_window[index] '''
        return self.multiplot_widget.find_plot_widget_by_label(label)
    
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
        self.producer_process.store.read()
        self.producer_process.store.flush()
        data = self.producer_process.read()
        self.plot(data)

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
        window = RegionPlotWindow(self)
        if len(self.multiplot_widget.plot_widgets) > 1:
            raise NotImplementedError('No support for over 2-dimensional data')
        for p in self.multiplot_widget.plot_widgets:
            # copy plot widget
            p_new = window.plot(x=p.x, y=p.y)
            p_new.y_label = p.y_label
        window.exec_()
    
    def start_button_clicked(self):
        '''
        Starts the producer process if is not None. Otherwise, nothing happens.
        Ok button is disabled. Emits signal: started.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        if self.producer_process is None:
            QMessageBox.critical(self, 'Error', 'No producer process defined')
            return
        self.update_timer.start(self.update_interval * 1000)
        self.producer_process.start()
        self.started.emit()
        self.ok_button.setEnabled(False)
        
    def stop_button_clicked(self):
        '''
        Stop the producer process if is not None. Otherwise, nothing happens.
        Ok button is enabled. Emits signal: stopped.
        
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
        self.ok_button.setEnabled(True)


class RegionPlotWindow(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.region_widget = RegionPlotWidget()
        self.ok_button = QPushButton('Ok')
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Region window')
        self.setLayout(self.layout)
        self.layout.addWidget(self.region_widget)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        
    def __getattr__(self, attr):
        ''' Object composition from self.region_widget (RegionPlotWidget) '''
        if attr in {'__getstate__', '__setstate__'}:
            return object.__getattr__(self, attr)
        return getattr(self.region_widget, attr)

    def ok_button_clicked(self):
        n = len(self.region_edit_map)
        msg = f'You have selected {n} regions. Are you sure you want to continue?'
        if QMessageBox.question(self, 'Are you sure?', msg) == QMessageBox.Yes:
            self.close()
