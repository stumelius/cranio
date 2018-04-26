import string
from cranio.app.plot import PlotBase

def test_x_label():
    p = PlotBase()
    
    label_map = {None: ''}
    for c in string.printable:
        label_map[c] = c
        
    for i, o in label_map.items():
        p.x_label = i
        assert p.x_label == o
        
def test_y_label():
    p = PlotBase()
    
    label_map = {None: ''}
    for c in string.printable:
        label_map[c] = c
        
    for i, o in label_map.items():
        p.y_label = i
        assert p.y_label == o
        