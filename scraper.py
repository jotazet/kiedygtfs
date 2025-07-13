import asyncio
from typing import List, Dict, Set
from tqdm.asyncio import tqdm
from data_structures import Customer, RawStop, Departure, TripDetails, ScrapedData
from units import get_next_n_days
from collections import defaultdict

CONCURRENCY = 5

async def fetch_all_stops(client) -> List[RawStop]:
    try:
        resp = await client.get("/stops")
        resp.raise_for_status()
        stops_data = resp.json()["stops"]
        all_stops = [
            RawStop(
                stop[0],                # stop_id
                stop[1],                # code
                stop[2].lower().title(),# name: convert to lower then title case
                stop[3],                # lon
                stop[4],                # lat
            )
            for stop in stops_data
        ]
        print(f"Fetched {len(all_stops)} stops.")
        return all_stops
    except Exception as e:
        print(f"Error fetching stops: {e}")
        return []

async def fetch_all_trip_ids(client, all_stops: List[RawStop]) -> Dict[str, Set[str]]:
    trip_calendar: Dict[str, Set[str]] = defaultdict(set)
    dates = get_next_n_days(8)
    failed_stop_schedules = []
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def fetch_timetable(stop, date):
        url = f"/api/timetables/{stop.stop_id}?date={date}"
        async with semaphore:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                departures = resp.json().get("departures", [])
                for dep in departures:
                    trip_id = str(dep["trip_id"])
                    trip_calendar[trip_id].add(date.replace("-", ""))
            except Exception as e:
                failed_stop_schedules.append(
                    f"{stop.name} {stop.code} ({stop.stop_id}): {date} ({e})"
                )

    tasks = [
        fetch_timetable(stop, date)
        for stop in all_stops
        for date in dates
    ]

    for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching timetables"):
        await f

    if failed_stop_schedules:
        print("Errors while fetching timetables for some stops:")
        for error in failed_stop_schedules:
            print(f"- {error}")

    return trip_calendar

async def fetch_all_trip_details(client, trip_ids: List[str]) -> List[TripDetails]:
    all_trips_details: List[TripDetails] = []
    failed_trip_details: List[str] = []
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def fetch_trip(trip_id: str):
        url = f"/api/trip/{trip_id}/0"
        async with semaphore:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                trip_detail = TripDetails(
                    times=data.get("times", []),
                    direction=data.get("direction", ""),
                    line_name=data.get("line_name") or data.get("line", ""),
                    trip_id=trip_id
                )
                all_trips_details.append(trip_detail)
            except Exception:
                failed_trip_details.append(trip_id)

    tasks = [fetch_trip(trip_id) for trip_id in trip_ids]

    for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching trip details"):
        await f

    if failed_trip_details:
        print("Errors while fetching trip details:")
        for trip_id in failed_trip_details:
            print(f"- {trip_id}")

    return all_trips_details

async def run_scraping_pipeline(provider: Customer, client) -> ScrapedData | None:
    print("Step 1/3: Fetching stops...")
    all_stops = await fetch_all_stops(client)
    if not all_stops:
        print("No stops found. Aborting.")
        return None

    print("Step 2/3: Scanning timetables for trips...")
    trip_calendar = await fetch_all_trip_ids(client, all_stops)
    if not trip_calendar:
        print("No trips found. Aborting.")
        return None

    print("Step 3/3: Fetching trip details...")
    trip_ids = list(trip_calendar.keys())
    all_trips_details = await fetch_all_trip_details(client, trip_ids)
    if not all_trips_details:
        print("No trip details found. Aborting.")
        return None

    return ScrapedData(provider, all_stops, all_trips_details, trip_calendar)