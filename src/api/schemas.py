from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, FiniteFloat, model_validator

class WeatherPoint(BaseModel):
    timestamp: AwareDatetime
    wind_speed: FiniteFloat = Field(ge=0,le=75)
    temperature: FiniteFloat = Field(ge=-80,le=60)

class ForecastPoint(WeatherPoint):
    predicted_power: FiniteFloat = Field(ge=0,le=1)
    lower_power: FiniteFloat = Field(ge=0,le=1)
    upper_power: FiniteFloat = Field(ge=0,le=1)

class ForecastResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    turbine_id: str
    generated_at: AwareDatetime
    forecast_origin: AwareDatetime
    horizon_hours: Literal[24,48]
    forecast: List[ForecastPoint]
    weather: Dict[str,Any]
    agent: Dict[str,Any]
    warnings: List[str]

    @model_validator(mode='after')
    def complete_horizon(self):
        from datetime import timedelta
        if len(self.forecast)!=self.horizon_hours:
            raise ValueError('Forecast length mismatch')
        for i,p in enumerate(self.forecast):
            if p.timestamp!=self.forecast_origin+timedelta(hours=i):
                raise ValueError('Incomplete hourly forecast timeline')
            if not p.lower_power<=p.predicted_power<=p.upper_power:
                raise ValueError('Prediction interval inconsistent')
        return self

class RecalculateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    turbine_id: Literal['turbine_1','turbine_2']
    hours: Literal[24,48] = 48
    mode: Optional[Literal['replay','live']] = None
    forecast_origin: Optional[AwareDatetime] = None
    weather: Optional[List[WeatherPoint]] = Field(default=None,min_length=24,max_length=48)
    weather_issued_at: Optional[AwareDatetime] = None

    @model_validator(mode='after')
    def require_provenance(self):
        if self.weather is not None and self.weather_issued_at is None:
            raise ValueError('weather_issued_at is required for new weather input')
        if self.weather is not None and len(self.weather)!=self.hours:
            raise ValueError('Weather length must equal hours')
        return self


class AgentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    turbine_id: Literal['turbine_1','turbine_2'] = 'turbine_1'
    hours: Literal[24,48] = 48
    mode: Literal['replay','live'] = 'replay'
    forecast_origin: Optional[AwareDatetime] = None
    message: str = Field(default='Построй прогноз и оцени риски.', min_length=1, max_length=1500)

    @model_validator(mode='after')
    def validate_origin(self):
        if self.forecast_origin is not None:
            from src.config import utc
            import pandas as pd
            origin=utc(self.forecast_origin)
            now=pd.Timestamp.now(tz='UTC')
            if origin!=origin.floor('h'):
                raise ValueError('forecast_origin must be aligned to an hour')
            if self.mode=='replay' and origin>now:
                raise ValueError('Replay origin cannot be in the future')
            if self.mode=='live' and not now.floor('h')<=origin<=now.ceil('h'):
                raise ValueError('Live origin must be the current or next hour')
        return self
