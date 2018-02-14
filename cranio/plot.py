import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QLayout, QWidget, QWidgetItem, QSpacerItem,
                             QDialog, QLabel, QVBoxLayout)
# pyqtgraph style settings
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

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
        plot_widget = PlotWidget()
        plot_widget.y_label = label
        self.plot_widgets.append(plot_widget)
        self.main_layout.addWidget(plot_widget)
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