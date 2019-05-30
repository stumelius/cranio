from config import Config
from cranio.model import DistractorType


def test_default_distractor_is_kls_red():
    assert Config.DEFAULT_DISTRACTOR == DistractorType.KLS_RED