"""
.. todo:: Refactor GUI modules (#90)
"""
import logging
import pyqtgraph as pg
import pandas as pd
from typing import Tuple, List, Iterable
from functools import partial
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLayout, QWidget, QWidgetItem, QSpacerItem, QDialog, QLabel, QVBoxLayout, QPushButton, \
    QHBoxLayout, QDoubleSpinBox, QGroupBox, QMessageBox, QSpinBox, QGridLayout, QCheckBox
from cranio.database import AnnotatedEvent, DISTRACTION_EVENT_TYPE_OBJECT, Document, session_scope

# plot style settings
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# custom color palette for plots
color_palette = [(76, 114, 176), (85, 168, 104), (196, 78, 82), 
                 (129, 114, 178), (204, 185, 116), (100, 181, 205)]


def remove_widget_from_layout(layout: QLayout, widget: QWidget):
    """
    Remove widget from a layout.

    :param layout:
    :param widget:
    :return:
    """
    layout.removeWidget(widget)
    widget.deleteLater()


def clear_layout(layout: QLayout):
    """
    Clear a layout.

    :param layout:
    :return:
    """
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)

        if isinstance(item, QWidgetItem):
            item.widget().close()
        elif isinstance(item, QSpacerItem):
            pass
        else:
            clear_layout(item.layout())
        # remove item from layout
        layout.removeItem(item)


class PlotWidget(pg.PlotWidget):
    """ Widget for displaying a (real-time) plot """
    
    # default plot configuration
    plot_configuration = {'antialias': True, 'pen': pg.mkPen(color_palette[0])}
    
    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.x = []
        self.y = []
        self.init_ui()
        
    def init_ui(self):
        """ Initialize UI elements. """
        self.showGrid(True, True, 0.1)
        self.enable_interaction(False)
    
    @property
    def x_label(self):
        """ Plot x label property. """
        return self.getAxis('bottom').labelText
    
    @x_label.setter
    def x_label(self, value):
        if value is None:
            value = ''
        self.setLabel('bottom', value)
        
    @property
    def y_label(self):
        """ Plot y label property. """
        return self.getAxis('left').labelText
    
    @y_label.setter
    def y_label(self, value):
        if value is None:
            value = ''
        self.setLabel('left', value)
        
    def enable_interaction(self, enable: bool):
        """
        Enable/disable interaction.

        :param enable:
        :return:
        """
        self.setMouseEnabled(enable, enable)
        self.setMenuEnabled(enable)
        
    def clear_plot(self):
        """
        Clear the plot.

        :return:
        """
        self.x = []
        self.y = []
        return self.getPlotItem().clear()
    
    def plot(self, x: Iterable[float], y: Iterable[float], mode: str='o'):
        """
        Plot (x, y) data.

        :param x:
        :param y:
        :param mode: Plot mode ('o' = overwrite, 'a' = append)
        :return:
        :raises ValueError: if invalid plot mode argument
        """
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
    """ Widget for editing a LinearRegionItem and editing event meta data. """
    
    def __init__(self, parent: pg.LinearRegionItem, event_number: int, document: Document):
        """

        :param parent:
        :param event_number:
        :param document: Data parent document
        """
        super(RegionEditWidget, self).__init__()
        self.parent = parent
        self.event_number = event_number
        self.document = document
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
        """ Initialize UI elements. """
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

    def region(self) -> Tuple[float, float]:
        """
        Return region edges.

        :return:
        """
        return self.parent.getRegion()

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
                              event_num=self.event_number, document_id=self.document.document_id,
                              event_begin=self.left_edge(), event_end=self.right_edge(), annotation_done=self.is_done())
    
    def set_region(self, edges: Tuple[float, float]):
        """
        Set region edges.

        :param edges:
        :return:
        """
        self.parent.setRegion(edges)

    def set_bounds(self, bounds: Tuple[float, float]):
        """
        Set region bounds.

        :param bounds:
        :return:
        """
        self.parent.setBounds(bounds)

    def value_changed(self, widget: QDoubleSpinBox, value: float):
        """
        Update region edges.

        :param widget:
        :param value:
        :return:
        :raises ValueError: if invalid widget argument
        """
        old_edges = self.region()
        if widget == self.minimum_edit:
            new_edges = (max(old_edges), value)
        elif widget == self.maximum_edit:
            new_edges = (value, min(old_edges))
        else:
            ValueError('Invalid widget')
        self.set_region(new_edges)

    def region_changed(self):
        """
        Update minimum and maximum edit widget values.

        :return:
        """
        new_edges = self.region()
        self.minimum_edit.setValue(min(new_edges))
        self.maximum_edit.setValue(max(new_edges))


class RegionPlotWidget(QWidget):
    """ Plot widget with region selection and edit functionality. """
    
    def __init__(self, document: Document, parent=None):
        """
        :param document: Data parent document
        :param parent:
        """
        super().__init__(parent)
        self.document = document
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
        """ Initialize UI elements. """
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addLayout(self.edit_layout)
        self.add_layout.addWidget(self.add_count, 0, 0)
        self.add_layout.addWidget(self.add_button, 0, 1)
        self.add_layout.addWidget(self.remove_all_button, 1, 0, 1, 2)
        self.edit_layout.addLayout(self.add_layout)
        self.add_button.clicked.connect(self.add_button_clicked)
        self.remove_all_button.clicked.connect(self.remove_all)
    
    @property
    def x(self):
        """ Plot x values property. """
        return self.plot_widget.x
    
    @property
    def y(self):
        """ Plot y values property. """
        return self.plot_widget.y

    def plot(self, x, y, mode='o'):
        """
        Plot (x, y) data.

        :param x:
        :param y:
        :param mode: Plot mode ('o' = overwrite, 'a' = append)
        :return:
        """
        return self.plot_widget.plot(x, y, mode)

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
        """
        Find a linear region item that corresponds to a specified region edit widget.

        :param edit_widget:
        :return:
        :raises ValueError: if no matching region edit widget was found
        """
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
        edit_widget = RegionEditWidget(item, event_number=self.region_count()+1, document=self.document)
        edit_widget.remove_button.clicked.connect(partial(self.remove_region, edit_widget))
        self.edit_layout.insertWidget(self.edit_layout.count()-1, edit_widget)
        self.region_edit_map[item] = edit_widget
        return edit_widget
    
    def remove_region(self, edit_widget: RegionEditWidget):
        """
        Remove specified region from the plot.

        :param edit_widget:
        :return:
        """
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
        """
        Add a number of regions to the plot matching the number in the add spin box.
        The region edges are initialized so that the region widths are constant and the regions do not overlap.

        :return:
        """
        if len(self.x) == 0:
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
        """
        Remove all regions from the plot.

        :return:
        """
        for edit_widget in list(self.region_edit_map.values()):
            self.remove_region(edit_widget)

    def get_annotated_events(self) -> List[AnnotatedEvent]:
        """
        Return an AnnotatedEvent for each event region in the plot.

        :return:
        """
        return [self.get_region_edit(i).get_annotated_event() for i in range(self.region_count())]


class VMultiPlotWidget(QWidget):
    """ Display multiple plots in a vertical layout. """
    
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
        """ Initialize UI elements. """
        self.setLayout(self.main_layout)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.main_layout.addWidget(self.title_label)
        
    @property
    def title(self):
        """ Plot title property. """
        return self.title_label.text()
    
    @title.setter
    def title(self, value):
        self.title_label.setText(value)
    
    def find_plot_widget_by_label(self, label: str):
        """
        Find plot by its label.

        :param label: Plot label, or y-axis name
        :return:
        """
        for p in self.plot_widgets:
            if p.y_label == label:
                return p
    
    def add_plot_widget(self, label: str):
        """
        Add a plot.

        :param label: Plot label, or y-axis name
        :return:
        :raises ValueError: if a plot with the specified label already exists
        """
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

    def plot(self, df: pd.DataFrame, title: str='', mode: str='o'):
        """
        Plot a dataframe.

        :param df: Pandas DataFrame where index is the x axis.
        :param title: Plot title.
        :param mode:
        :return:
        """
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
        initialized_columns = [p.y_label for p in self.plot_widgets if p.y_label in df]
        # leftover columns need to be initialized
        non_initialized_columns = filter(lambda c: c not in initialized_columns, df.columns)
        for c in non_initialized_columns:
            self.add_plot_widget(c)
        # plot each column
        for c in df:
            plot_widget = self.find_plot_widget_by_label(c)
            plot_widget.plot(x=df.index, y=df[c], mode=mode)
    
    def clear(self):
        """
        Clear all plots.

        :return:
        """
        for p in self.plot_widgets:
            p.clear()
            
    def reset(self):
        """
        Remove all plots from the layout.

        :return:
        """
        for p in self.plot_widgets:
            remove_widget_from_layout(self.main_layout, p)
        self.plot_widgets = []


class RegionPlotWindow(QDialog):
    """ Dialog with a region plot widget and an "Ok" button. """
    
    def __init__(self, document: Document, parent=None):
        """

        :param document: Data parent document
        :param parent:
        """
        super().__init__(parent)
        self.document = document
        self.layout = QVBoxLayout()
        self.region_plot_widget = RegionPlotWidget(document=document)
        self.ok_button = QPushButton('Ok')
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.setWindowTitle('Region window')
        self.setLayout(self.layout)
        self.layout.addWidget(self.region_plot_widget)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        # plot document data
        self.plot(*self.document.get_related_time_series())

    def ok_button_clicked(self, user_prompt: bool=True):
        """

        :param user_prompt: Indicate if user is to be prompted for verification to continue.
        False can be used for testing purposes.
        :return:
        """
        msg = f'You have selected {self.region_plot_widget.region_count()} regions. Are you sure you want to continue?'
        if user_prompt:
            if not QMessageBox.question(self, 'Are you sure?', msg) == QMessageBox.Yes:
                return
        # insert annotated events to local database
        events = self.region_plot_widget.get_annotated_events()
        with session_scope() as s:
            for e in events:
                s.add(e)
        self.close()

    @property
    def x(self):
        """ Overload property. """
        return self.region_plot_widget.x

    @property
    def y(self):
        """ Overload property. """
        return self.region_plot_widget.y

    def plot(self, x, y):
        """ Overload method. """
        return self.region_plot_widget.plot(x, y)

    def set_add_count(self, value: int):
        """ Overload method. """
        return self.region_plot_widget.set_add_count(value)

    def add_button_clicked(self):
        """ Overload method. """
        return self.region_plot_widget.add_button_clicked()

    def get_region_edit(self, index: int):
        """ Overload method. """
        return self.region_plot_widget.get_region_edit(index)

    def region_count(self) -> int:
        """ Overload method. """
        return self.region_plot_widget.region_count()

