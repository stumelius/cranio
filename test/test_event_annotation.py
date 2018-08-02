'''
List of tests:
* (check) Annotated event can be flagged as undone and unrecorded
' (check) Done checkbox is unchecked by default
* (check) Recorded checkbox is checked by default
* (check) Checking and unchecking Done checkbox toggles Done state
* (check) Checking and unchecking Recorded checkbox toggles Recorded state
* (check) Annotated event number matches region edit widget number
* (check) Region count is zero when no regions are added
* (check) Event numbering starts from one
* (check) Event number increases by one for each added region
* (check) Event numbering by insertion order
* (check) Region edit widget is assigned parent region plot widget documenta
'''
import pytest
import numpy as np
from typing import Iterable, List
from cranio.database import AnnotatedEvent, Document, Measurement, session_scope, EventType
from cranio.app.widget import RegionPlotWidget, RegionEditWidget
from cranio.app.window import RegionPlotWindow


left_edge = 0
right_edge = 99
region_count = 4
wait_msec = 500


@pytest.fixture
def region_plot_widget():
    widget = RegionPlotWidget()
    # plot random data
    x = np.linspace(left_edge, right_edge, 100)
    y = np.random.rand(len(x))
    widget.plot(x, y)
    # add regions using add button
    widget.set_add_count(region_count)
    widget.add_button_clicked()
    yield widget


def add_dummy_region(widget: RegionPlotWidget) -> RegionEditWidget:
    """ Helper function. """
    return widget.add_region((left_edge, (left_edge + right_edge) / 2))


def test_annotated_event_can_be_flagged_as_undone_and_not_recorded(database_document_fixture):
    document_id = Document.get_instance().document_id
    event_type = EventType.distraction_event_type().event_type
    annotated_event = AnnotatedEvent(event_num=1, event_type=event_type, document_id=document_id, annotation_done=False,
                                     recorded=False)
    assert not annotated_event.annotation_done


def test_done_checkbox_is_unchecked_by_default(region_plot_widget):
    assert not region_plot_widget.get_region_edit(0).is_done()


def test_recorded_checkbox_is_checked_by_default(region_plot_widget):
    assert region_plot_widget.get_region_edit(0).is_recorded()


def test_checking_and_unchecking_done_checkbox_toggles_done_state(region_plot_widget):
    # check Done in each region edit widget
    for i in range(region_count):
        edit_widget = region_plot_widget.get_region_edit(i)
        edit_widget.set_done(True)
        assert edit_widget.is_done()
        edit_widget.set_done(False)
        assert not edit_widget.is_done()


def test_checking_and_unchecking_recorded_checkbox_toggles_done_state(region_plot_widget):
    # check Recorded state in each region edit widget
    for i in range(region_count):
        edit_widget = region_plot_widget.get_region_edit(i)
        edit_widget.set_recorded(False)
        assert not edit_widget.is_recorded()
        edit_widget.set_recorded(True)
        assert edit_widget.is_recorded()


def test_annotated_event_number_matches_region_edit_widget_number(region_plot_widget):
    for i in range(region_count):
        edit_widget = region_plot_widget.get_region_edit(i)
        event = edit_widget.get_annotated_event()
        assert event.event_num == edit_widget.event_number


def test_region_count_is_zero_when_no_regions_are_added(region_plot_widget):
    # remove all regions
    region_plot_widget.remove_all()
    assert region_plot_widget.region_count() == 0


def test_event_numbering_starts_from_one(region_plot_widget):
    # remove all regions
    region_plot_widget.remove_all()
    edit_widget = add_dummy_region(region_plot_widget)
    assert edit_widget.event_number == 1


def test_event_number_increases_by_one_for_each_added_region(region_plot_widget):
    # remove all regions
    region_plot_widget.remove_all()
    for i in range(region_count):
        edit_widget = add_dummy_region(region_plot_widget)
        assert edit_widget.event_number == i+1


def test_event_numbering_by_insertion_order(region_plot_widget):
    # remove all regions
    region_plot_widget.remove_all()
    # add 4 regions
    for i in range(4):
        edit_widget = add_dummy_region(region_plot_widget)
    assert edit_widget.event_number == 4
    # remove 2
    edit_widget = region_plot_widget.remove_at(index=3)
    assert edit_widget.event_number == 4
    edit_widget = region_plot_widget.remove_at(index=2)
    assert edit_widget.event_number == 3
    # add 1
    edit_widget = add_dummy_region(region_plot_widget)
    assert edit_widget.event_number == 3


def insert_time_series_to_database(time_s: Iterable[float], torque_Nm: Iterable[float],
                                   document: Document) -> List[Measurement]:
    """ Helper function. """
    measurements = []
    with session_scope() as s:
        for x, y in zip(time_s, torque_Nm):
            m = Measurement(document_id=document.document_id, time_s=x, torque_Nm=y)
            measurements.append(m)
            s.add(m)
    return measurements


def test_region_plot_window_can_be_initialized_from_document_data(database_document_fixture):
    # generate data and associate with document
    n = 100
    document = Document.get_instance()
    X = np.linspace(left_edge, right_edge, n)
    Y = np.random.rand(n)
    insert_time_series_to_database(X, Y, document)
    region_plot_window = RegionPlotWindow()
    region_plot_window.plot(*document.get_related_time_series())
    np.testing.assert_array_almost_equal(region_plot_window.x_arr, X)
    np.testing.assert_array_almost_equal(region_plot_window.y_arr, Y)


def test_annotated_events_inserted_to_database_after_ok_on_region_plot_window_is_clicked():
    # generate data and associate with document
    n = 100
    document = Document.get_instance()
    X = np.linspace(left_edge, right_edge, n)
    Y = np.random.rand(n)
    insert_time_series_to_database(X, Y, document)
    region_plot_window = RegionPlotWindow()
    region_plot_window.plot(*document.get_related_time_series())
    # add regions using add button
    region_plot_window.set_add_count(region_count)
    region_plot_window.add_button_clicked()
    # verify that annotated events are correct
    events = region_plot_window.get_annotated_events()
    assert len(events) == region_count

"""
* Annotated event can be flagged as not recorded
* Recorded checkbox is checked by default
* Checking and unchecking Recorded checkbox toggles Recorded state
"""