from typing import List, Dict, Set

class Customer:
    def __init__(self, name: str, prefix: str, domain: str):
        self.name = name
        self.prefix = prefix
        self.domain = domain

class RawStop:
    def __init__(self, stop_id: str, code: int, name: str, lon: float, lat: float):
        self.stop_id = stop_id
        self.code = code
        self.name = name
        self.lon = lon
        self.lat = lat

class Departure:
    def __init__(self, trip_id: int):
        self.trip_id = trip_id

class TripDetails:
    def __init__(self, times: List[Dict[str, str]], direction: str, line_name: str, trip_id: str):
        self.times = times
        self.direction = direction
        self.line_name = line_name
        self.trip_id = trip_id

class ScrapedData:
    def __init__(self, provider: Customer, stops: List[RawStop], trips: List[TripDetails], trip_calendar: Dict[str, Set[str]]):
        self.provider = provider
        self.stops = stops
        self.trips = trips
        self.trip_calendar = trip_calendar
