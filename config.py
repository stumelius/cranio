import os
from cranio.model import DistractorType


class Config:
    DEFAULT_DISTRACTOR = os.getenv('CRANIO_DEFAULT_DISTRACTOR', DistractorType.KLS_RED)
    ENABLE_DUMMY_SENSOR = os.getenv('CRANIO_ENABLE_DUMMY_SENSOR', False)
