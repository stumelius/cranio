import pytest
from cranio.model import session_scope, Session
from cranio.app.widget import SessionWidget


@pytest.fixture
def session_widget(database_fixture):
    # Initialize two sessions
    pytest.helpers.add_session(database_fixture)
    pytest.helpers.add_session(database_fixture)
    session_widget = SessionWidget(database=database_fixture)
    yield session_widget


def test_session_widget_contains_all_sessions_from_the_database(session_widget):
    assert session_widget.session_count() == 2
    assert len(session_widget.sessions) == 2


def test_session_widget_select_and_click_ok_changes_active_session(session_widget):
    with session_scope(session_widget.database) as s:
        session = s.query(Session).first()
    assert session_widget.session_id != session.session_id
    session_widget.select_session(session_id=session.session_id)
    assert session_widget.session_id == session.session_id
