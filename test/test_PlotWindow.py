
from pyqtgraph import PlotWidget
from craniodistractor.app.plot import PlotWindow, RegionWidget

def test_add_get_and_remove_plot():
    p = PlotWindow()
    widgets = [PlotWidget(), RegionWidget()]
    for w in widgets:
        p.add_plot(w)
    for i, w in enumerate(widgets):
        assert p[i] == w
        assert w in p
    for w in widgets:
        p.remove_plot(w)
        assert w not in p
        
