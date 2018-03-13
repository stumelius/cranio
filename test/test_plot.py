import string
import random
import pytest
import numpy as np
import pandas as pd
from functools import partial
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QApplication, QMessageBox
from cranio.app import app
from cranio.app.plot import (PlotWidget, VMultiPlotWidget, PlotWindow,
                             RegionPlotWidget, RegionPlotWindow)

def test_PlotWidget_overwrite():
    w = PlotWidget()
    for i in range(10):
        x = np.random.rand(i)
        y = np.random.rand(i)
        w.plot(x, y, 'o')
        assert w.x == list(x)
        assert w.y == list(y)
    w.clear_plot()
    assert w.x == []
    assert w.y == []

def test_PlotWidget_append():
    w = PlotWidget()
    X = []
    Y = []
    for i in range(10):
        x = np.random.rand(i)
        y = np.random.rand(i)
        X += list(x)
        Y += list(y)
        w.plot(x, y, 'a')
        assert w.x == X
        assert w.y == Y
    w.clear_plot()
    assert w.x == []
    assert w.y == []

def test_PlotWidget_dtypes():
    w = PlotWidget()
    x = [random.random() for _ in range(10)]
    y = [random.random() for _ in range(10)]
    
    def _assert_plot(x_in, y_in):
        w.plot(x, y, 'o')
        assert w.x == list(x)
        assert w.y == list(y)
    # numpy array
    x_np = np.array(x)
    y_np = np.array(y)
    _assert_plot(x_np, y_np)
    # pandas series
    x_pd = pd.Series(x)
    y_pd = pd.Series(y)
    w.plot(x_pd, y_pd, 'o')
    _assert_plot(x_pd, y_pd)
 
def test_PlotWidget_x_label():
    p = PlotWidget()
    
    label_map = {None: ''}
    for c in string.printable:
        label_map[c] = c
        
    for i, o in label_map.items():
        p.x_label = i
        assert p.x_label == o, 'x_label: {} - output: {} (input: {})'.format(p.x_label, o, i)

def test_PlotWidget_y_label():
    p = PlotWidget()
    
    label_map = {None: ''}
    for c in string.printable:
        label_map[c] = c
        
    for i, o in label_map.items():
        p.y_label = i
        assert p.y_label == o, 'y_label: {} - output: {} (input: {})'.format(p.y_label, o, i)

@pytest.mark.parametrize('rows', [100, 1000])
def test_VMultiPlotWidget_plot_and_overwrite(rows):
    p = VMultiPlotWidget()
    for _ in range(2):
        data = pd.DataFrame(np.random.rand(rows, 4), 
                            columns=list('ABCD'))
        p.plot(data, 'title', mode='o')
        assert p.title == 'title'
        assert len(p.plot_widgets) == 4
        
        # assert data in each plot widget
        for c in data.columns:
            pw = p.find_plot_widget_by_label(c)
            assert pw.x == data[c].index.tolist()
            assert pw.y == data[c].tolist()
            
def test_VMultiPlotWidget_placeholder():
    p = VMultiPlotWidget()
    assert p.placeholder is not None
    plot_widget = p.add_plot_widget('foo')
    assert p.placeholder is None
    assert p.find_plot_widget_by_label('foo') == plot_widget
            
def test_PlotWindow_show():
    p = PlotWindow(producer_process=None)
    p.show()
    
def test_RegionPlotWidget_add_region():
    region_widget = RegionPlotWidget()
    n = 100
    region_widget.plot(x=list(range(n)), y=list(range(n)))
    for top in range(0,51,10):
        region = [0, top]
        edit_widget = region_widget.add_region(region)
        assert edit_widget.region() == tuple(region)
        edit_widget.set_region([0,1])
        assert edit_widget.region() == (0,1)
    for widget in region_widget.region_edit_map.values():
        assert widget.region() == (0,1)
        
def test_RegionPlotWidget_remove_region():
    region_widget = RegionPlotWidget()
    n = 100
    region_widget.plot(x=list(range(n)), y=list(range(n)))
    item = region_widget.add_region([0,10])
    assert len(region_widget.region_edit_map) == 1
    region_widget.remove_region(item)
    assert len(region_widget.region_edit_map) == 0
    
def test_RegionPlotWidget_set_bounds():
    region_widget = RegionPlotWidget()
    n = 100
    region_widget.plot(x=list(range(n)), y=list(range(n)))
    edit_widget = region_widget.add_region([0,50])
    assert edit_widget.region() == (0,50)
    edit_widget.set_bounds([0,10])
    assert edit_widget.region() == (0,10)
    edit_widget.set_bounds([0,100])
    assert edit_widget.region() == (0,10)
    edit_widget.set_region([0,50])
    assert edit_widget.region() == (0,50)
    
def test_RegionPlotWindow_ok_button():
    d = RegionPlotWindow()
    n = 100
    d.plot(x=list(range(n)), y=list(range(n)))
    assert len(d.region_edit_map) == 0
    d.add_button_clicked()
    assert len(d.region_edit_map) == 1
    def click_button(standard_button):
        w = QApplication.activeWindow()
        b = w.button(standard_button)
        b.clicked.emit()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.setInterval(100)
    timer.timeout.connect(partial(click_button, QMessageBox.Yes))
    timer.start()
    d.show()
    assert d.isVisible()
    d.ok_button_clicked()
    assert not d.isVisible()