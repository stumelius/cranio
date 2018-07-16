'''
List of tests:
* (check) Annotated event can be flagged as undone
' (check) Done checkbox is unchecked by default
* (check) Checking and unchecking Done checkbox toggles Done state
* (check) Annotated event number matches region edit widget number
* (check) Region count is zero when no regions are added
* (check) Event numbering starts from one
* (check) Event number increases by one for each added region
* (check) Event numbering by insertion order
* (check) Region edit widget is assigned parent region plot widget document
'''
import pytest
import numpy as np
from cranio.database import AnnotatedEvent, Document, DISTRACTION_EVENT_TYPE_OBJECT
from cranio.app.plot import RegionPlotWidget, RegionEditWidget


left_edge = 0
right_edge = 99
region_count = 4


@pytest.fixture
def region_plot_widget():
    # create dummy document
    document = Document()
    widget = RegionPlotWidget(document=document)
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


def test_annotated_event_can_be_flagged_as_undone(database_document_fixture):
    document_id = Document.get_instance()
    event_type = DISTRACTION_EVENT_TYPE_OBJECT.event_type
    annotated_event = AnnotatedEvent(event_num=1, event_type=event_type, document_id=document_id, annotation_done=False)
    assert not annotated_event.annotation_done


def test_done_checkbox_is_unchecked_by_default(region_plot_widget):
    assert not region_plot_widget.get_region_edit(0).is_done()


def test_checking_and_unchecking_done_checkbox_toggles_done_state(region_plot_widget):
    # check Done in each region edit widget
    for i in range(region_count):
        edit_widget = region_plot_widget.get_region_edit(i)
        edit_widget.set_done(True)
        assert edit_widget.is_done()
        edit_widget.set_done(False)
        assert not edit_widget.is_done()


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


def test_region_edit_widget_is_assigned_parent_region_plot_widget_document(region_plot_widget):
    for i in range(region_count):
        edit_widget = region_plot_widget.get_region_edit(i)
        assert region_plot_widget.document == edit_widget.document