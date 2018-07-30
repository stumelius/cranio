import pytest
from cranio.database import Document
from cranio.app.window import NotesWindow


@pytest.fixture
def notes_window(database_document_fixture):
    document = Document.get_instance()
    window = NotesWindow(document=document)
    yield window


def test_notes_window_set_notes_sets_document_notes(notes_window):
    notes = 'apples and oranges'
    notes_window.notes = notes
    assert notes_window.document.notes == notes


def test_notes_window_set_distraction_achieved(notes_window):
    distraction_achieved = 1.2
    notes_window.distraction_achieved = distraction_achieved
    assert notes_window.document.distraction_achieved == distraction_achieved


def test_notes_window_set_distraction_plan_followed(notes_window):
    distraction_plan_followed = True
    notes_window.distraction_plan_followed = distraction_plan_followed
    assert notes_window.document.distraction_plan_followed == distraction_plan_followed
