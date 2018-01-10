import random
import pytest
import string

from cranio.app.dialogs import MeasurementDialog

def test_MeasurementDialog_set_and_get_distractor_index():
    d = MeasurementDialog()
    
    # integers
    for i in range(20):
        d.distractor_index = i
        assert d.distractor_index == i
    
    # floats
    for _ in range(20):
        i = random.random()
        with pytest.raises(ValueError):
            d.distractor_index = i
            
    # characters
    for s in string.printable:
        with pytest.raises(ValueError):
            d.distractor_index = s