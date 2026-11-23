from enum import StrEnum


class Role(StrEnum):
    admin = 'admin'
    analyst = 'analyst'
    viewer = 'viewer'


class Band(StrEnum):
    early = 'early'
    day = 'day'
    late = 'late'


class HVAC(StrEnum):
    quiet = 'quiet'
    normal = 'normal'
    boost = 'boost'


class Position(StrEnum):
    booth = 'booth'
    street = 'street'
    door = 'door'


class Predictor(StrEnum):
    traffic = 'traffic'
    hvac = 'hvac'


class Control(StrEnum):
    band = 'band'
    hvac = 'hvac'
    position = 'position'
    session = 'session'


HVAC_RANK = {setting.value: rank for rank, setting in enumerate(HVAC)}
