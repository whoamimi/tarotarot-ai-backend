# src/schemas/astrology.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from zoneinfo import ZoneInfo

from immanuel import charts
from immanuel.const import chart
from utils.handler import get_lat_lon


class UserInsights(BaseModel):
    """ Astrology & Natal House Placements of the user. """
    
    sun_sign: str = 'UNKNOWN'
    moon_sign: str = 'UNKNOWN'
    rising_sign: str = 'UNKNOWN'
    house_placements: dict[str, Optional[str]] | str = {}
    elemental_distribution: dict[str, int] = {}
    modality_distribution: dict[str, int] = {}
    dominant_planets: dict[str, int] = {}

    @field_validator('sun_sign', 'moon_sign', 'rising_sign', mode='before')
    @classmethod
    def normalize_sign(cls, v):
        if v is None:
            return 'UNKNOWN'
        return str(v).strip().title()

    def compute_from_datetime(self, dt: datetime, birth_place: str | None = "Australia/Sydney"):
        """
        Populate astrology fields given a timezone-aware datetime and a birth_place string.
        This method mutates self and returns None.
        """
        if dt.tzinfo is None:
            # If dt is naive, attach explicit zoneinfo from birth_place
            tz = ZoneInfo(birth_place)
            dt = dt.replace(tzinfo=tz)

        latitude, longitude = get_lat_lon(place=birth_place)
        native = charts.Subject(date_time=dt, latitude=latitude, longitude=longitude)
        natal = charts.Natal(native)

        self.sun_sign = natal.objects[chart.SUN].sign.name
        self.moon_sign = natal.objects[chart.MOON].sign.name
        self.rising_sign = natal.objects[chart.ASC].sign.name

        self.house_placements = {
            f"{i}th House": natal.houses.get(str(i)).sign.name
            if natal.houses.get(str(i)) and getattr(natal.houses.get(str(i)), "sign", None) is not None
            else None
            for i in range(1, 13)
        }

        elements: dict[str, int] = {}
        modalities: dict[str, int] = {}
        dominant_planets: dict[str, int] = {}

        for obj in natal.objects.values():
            if obj.type.name == 'Planet':
                element = obj.sign.element
                modality = obj.sign.modality
                planet = obj.name

                elements[element] = elements.get(element, 0) + 1
                modalities[modality] = modalities.get(modality, 0) + 1
                dominant_planets[planet] = dominant_planets.get(planet, 0) + 1

        self.elemental_distribution = elements
        self.modality_distribution = modalities
        self.dominant_planets = dominant_planets