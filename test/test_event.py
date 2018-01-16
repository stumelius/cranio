import pytest

from cranio.core import Event, event_identifier

def test_valid_events():
    event_map = {(Event.DISTRACTION, 1): 'D001',
                 (Event.DISTRACTION, 12): 'D012',
                 (Event.DISTRACTION, 123): 'D123',
                 (Event.DISTRACTION, 0): 'D000',
                 (Event.DISTRACTION, 999): 'D999'}
    for key, value in event_map.items():
        event = Event(*key)
        assert str(event) == value
        
def test_events_too_high_or_negative_num():
    with pytest.raises(ValueError):
        event = Event(Event.DISTRACTION, 1000)
    with pytest.raises(ValueError):
        event = Event(Event.DISTRACTION, -1)
        
def test_events_wrong_data_type():
    events = [(1, 1), ('s', 0.1), (1, 0.1)]
    for args in events:
        with pytest.raises(TypeError):
            event = Event(*args)