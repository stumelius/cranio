import pytest
import random

from cranio.app.plot import PlotWindow, RegionWidget

random.seed(1)

@pytest.fixture()
def window():
    w = PlotWindow()
    w.add_plot(RegionWidget())
    x = list(range(100))
    y = [random.gauss(0,1) for _ in range(len(x))]
    w.get_plot().plot(x, y)
    return w

def test_add_region(window):
    w = window
    region_widget = w.get_plot()
    for top in range(0,51,10):
        region = [0, top]
        edit_widget = region_widget.add_region(region)
        assert edit_widget.region() == tuple(region)
        edit_widget.set_region([0,1])
        assert edit_widget.region() == (0,1)
    for widget in region_widget.region_edit_map.values():
        assert widget.region() == (0,1)
    w.show()
    
def test_remove_region(window):
    w = window
    region_widget = w.get_plot()
    item = region_widget.add_region([0,10])
    assert len(region_widget.region_edit_map) == 1
    region_widget.remove_region(item)
    #assert len(w.region_widget.region_items) == 0
    w.show()
    
    
def test_set_bounds(window):
    w = window
    
    edit_widget = w.get_plot().add_region([0,50])
    assert edit_widget.region() == (0,50)
    edit_widget.set_bounds([0,10])
    assert edit_widget.region() == (0,10)
    edit_widget.set_bounds([0,100])
    assert edit_widget.region() == (0,10)
    edit_widget.set_region([0,50])
    assert edit_widget.region() == (0,50)
    