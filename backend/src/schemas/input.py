from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from src.constants.labels import Band, Control, HVAC, Position, Predictor

Title = Annotated[str, StringConstraints(min_length=1, max_length=80)]
Note = Annotated[str, StringConstraints(max_length=350)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)


class Login(Input):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class Session(Input):
    code: str = Field(pattern=r'^[A-Z0-9][A-Z0-9-]{0,23}$')
    title: Title
    recorded_on: date = Field(ge=date(2000, 1, 1), le=date(2100, 12, 31))
    start_time: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    band: Band
    room: str = Field(min_length=1, max_length=48)
    note: Note = ''


class Reading(Input):
    session_id: int = Field(gt=0)
    reference: str = Field(min_length=1, max_length=64)
    hvac: HVAC
    position: Position
    traffic: int = Field(ge=0, le=1000)
    noise: float = Field(ge=0, le=140, multiple_of=0.01)
    note: Note = ''


class Method(Input):
    version: str = Field(pattern=r'^[A-Z0-9][A-Z0-9.-]{0,31}$')
    title: Title
    predictor: Predictor
    controls: list[Control] = Field(max_length=4)
    note: Note = ''

    @model_validator(mode='after')
    def check_controls(self):
        if len(set(self.controls)) != len(self.controls):
            raise ValueError('控制量不可重复')
        if self.predictor in self.controls:
            raise ValueError('不能同时作为解释量和控制量')
        return self


class Diagnostic(Input):
    title: Title
    method_id: int = Field(gt=0)
    session_ids: list[int] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def unique_sessions(self):
        if min(self.session_ids) < 1 or len(set(self.session_ids)) != len(self.session_ids):
            raise ValueError('时段编号必须为正整数，且不可重复')
        return self


class Acceptance(Input):
    title: Title
    pre_session_ids: list[int] = Field(min_length=1, max_length=100)
    post_session_ids: list[int] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def disjoint_sessions(self):
        ids = self.pre_session_ids + self.post_session_ids
        if min(ids) < 1 or len(set(ids)) != len(ids):
            raise ValueError('时段编号必须为正整数，且同一时段不能算进两期')
        return self


class Decision(Input):
    text: str = Field(min_length=8, max_length=500)
