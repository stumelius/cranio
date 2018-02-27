import string
import random
import pytest
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets
from cranio.app import app
from cranio.plot import PlotWidget, VMultiPlotWidget, PlotWindow

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
            
def test_PlotWindow_show():
    p = PlotWindow(producer_process=None)
    p.show()