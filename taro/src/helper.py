"""
src/data_processor.py

Data processors to augment and transform certain fields of the dataset before / after storing and retrieval.

BeforeValidator – Preprocessing input values: Use this when you want to clean or coerce the input before Pydantic validates or parses it.
AfterValidator – Post-processing or fixing values: when you want to modify or validate a value after its been parsed

"""

from datetime import datetime
from typing import Annotated
from geopy.geocoders import Nominatim
from pydantic.functional_validators import BeforeValidator, AfterValidator

from utils.woodpecker import setup_logger

logger = setup_logger(__name__)

DEFAULT_DATE_FORMAT = "%d-%m-%Y"
DEFAULT_TIME_FORMAT = "%H:%M"

def parse_datetime(input_date: str | datetime) -> datetime | None:
    try:
        if isinstance(input_date, str):
            return datetime.strptime(input_date, DEFAULT_DATE_FORMAT)
        elif isinstance(input_date, datetime):
            return input_date
    except Exception as e:
        logger.error(e)
        raise

def parse_timestamp(input_time: str | datetime) -> datetime | None:
    try:
        if isinstance(input_time, str):
            return datetime.strptime(input_time, DEFAULT_TIME_FORMAT) # type: ignore
        elif isinstance(input_time, datetime):
            return input_time
    except Exception as e:
        logger.error(e)
        raise

def get_lat_lon(place: str):
    """ Gets Latitude and Longitude"""
    geolocator = Nominatim(user_agent="astro-app")
    location = geolocator.geocode(place)
    if location:
        return location.latitude, location.longitude # type: ignore
    else:
        raise ValueError(f"Could not geocode location: {place}")

IncommingDate = Annotated[datetime | str, BeforeValidator(parse_datetime)]
IncommingTimestamp = Annotated[datetime | str | None, BeforeValidator(parse_timestamp)]
DisplayName = Annotated[str | None, BeforeValidator(lambda x: x.strip().title() if isinstance(x, str) else None)]

