# src/schemas/user.py
from uuid import uuid4
from datetime import datetime, time
from zoneinfo import ZoneInfo
from pydantic import BaseModel, field_serializer, model_validator, ConfigDict

from utils.handler import IncommingDate, IncommingTimestamp, DisplayName
from src.schemas.astrology import UserInsights  # relative import into the new package

class User(UserInsights):
    """User profile that includes astrology (inherits UserInsights)."""

    id: str
    username: str
    first_name: DisplayName
    last_name: DisplayName
    birth_date: IncommingDate  # processed into datetime during validation
    birth_time: IncommingTimestamp = None
    birth_place: str | None = 'Australia/Sydney'
    gender: str | None = 'UNKNOWN'

    model_config = ConfigDict(
        json_encoders={ datetime: lambda dt: dt.isoformat() }
    )

    @field_serializer('birth_date', mode='plain')
    def _ser_birth_date(self, v: datetime, _info) -> str:
        # e.g. 1998-07-27
        return v.strftime('%Y-%m-%d')

    @field_serializer('birth_time', mode='plain')
    def _ser_birth_time(self, v: datetime | None, _info) -> str | None:
        if not v:
            return None
        return v.isoformat()

    @model_validator(mode='after')
    def validate_user_profile(self):
        """
        Ensure birth_date & birth_place exist and coerce/normalize birth_date + birth_time
        into timezone-aware datetimes. Then delegate astrology computation to UserInsights.
        """
        if not self.birth_date or not self.birth_place:
            raise ValueError(f"Expected 'birth_date' and 'birth_place' to be non-null; got birth_date={self.birth_date}, birth_place={self.birth_place}")

        if isinstance(self.birth_date, str):
            raise ValueError(f"Processing birth_date failed — expected a datetime, received string: {self.birth_date} (type={type(self.birth_date)})")

        # If birth_time provided as datetime, extract its time with TZ when possible
        if self.birth_time and isinstance(self.birth_time, datetime):
            tz = ZoneInfo(self.birth_place)
            bt = self.birth_time.replace(tzinfo=tz).time()
        else:
            tz = ZoneInfo(self.birth_place)
            bt = time(0, 0)

        dt = datetime.combine(self.birth_date, bt).replace(tzinfo=tz)

        # Overwrite both fields so they're fully tz-aware datetimes
        self.birth_time = dt
        self.birth_date = dt

        # Compute astrology fields using the dedicated method on UserInsights
        self.compute_from_datetime(dt, self.birth_place or "Australia/Sydney")
        return self

    @property
    def birth(self) -> datetime:
        """Return the full timezone-aware datetime for the user's birth."""
        if isinstance(self.birth_time, datetime):
            timestamp = self.birth_date.time()  # type: ignore
        else:
            timestamp = datetime.now().time()
        return datetime.combine(self.birth_date.date(), timestamp).replace(tzinfo=ZoneInfo(self.birth_place))