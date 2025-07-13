import os
import csv
import io
import zipfile
from tqdm import tqdm
from units import time_to_seconds, seconds_to_time

def load_vehicle_trip_settings(file_path: str) -> dict[tuple[str, str], int]:
    settings = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("route_id"):
                    continue
                parts = line.split(",")
                if len(parts) < 4:
                    continue
                route_id, organization, _, route_type = parts
                settings[(route_id.strip(), organization.strip().lower())] = int(route_type.strip())
    except Exception as e:
        print(f"Error loading vehicle trip settings: {e}")
    return settings

def load_route_color_settings(file_path: str) -> dict[str, str]:
    settings = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.lower().startswith("agency_id"):
                    continue
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                agency_id, colour = parts[0].strip(), parts[1].strip()
                settings[agency_id.lower()] = colour if colour else "FFFFFF"
    except Exception as e:
        print(f"Error loading route color settings: {e}")
    return settings

def generate_gtfs(data):
    print("Preparing data for GTFS format...")
    if not data.trips:
        print("No trip details available, GTFS file will not be generated.")
        return

    file_name = f"{data.provider.prefix}.gtfs.zip"
    zip_path = os.path.join(os.getcwd(), file_name)
    vehicle_settings = load_vehicle_trip_settings("vehicle_routes_settings.txt")
    route_color_settings = load_route_color_settings("vehicle_routes_settings.txt")
    
    def csv_string(rows, fieldnames):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # agency.txt
        agency_rows = [{
            "agency_id": data.provider.prefix,
            "agency_name": data.provider.name,
            "agency_url": f"https://{data.provider.prefix}.{data.provider.domain}",
            "agency_timezone": "Europe/Warsaw",
            "agency_lang": "pl",
        }]
        zf.writestr("agency.txt", csv_string(agency_rows, agency_rows[0].keys()))

        # stops.txt
        stops_rows = [{
            "stop_id": str(stop.stop_id).split(":")[1] if ":" in str(stop.stop_id) else str(stop.stop_id),
            "stop_code": stop.code,
            "stop_name": stop.name,
            "stop_lon": stop.lon / 1e6,
            "stop_lat": stop.lat / 1e6,
        } for stop in data.stops]
        zf.writestr("stops.txt", csv_string(stops_rows, stops_rows[0].keys()))

        # routes, trips, stop_times, calendar_dates
        routes = {}
        trips = []
        stop_times = []
        calendar_dates = []

        for trip_detail in tqdm(data.trips, desc="Processing trips"):
            route_id = trip_detail.line_name or "unknown"
            if isinstance(route_id, dict):
                route_id = route_id.get("name")
            if not route_id:
                route_id = "unknown"

            if route_id not in routes:
                routes[route_id] = {
                    "route_id": route_id,
                    "agency_id": data.provider.prefix,
                    "route_short_name": route_id,
                    "route_type": 3,
                    "route_color": route_color_settings.get(data.provider.prefix.lower(), "FFFFFF"),
                }

            trip_id = trip_detail.trip_id
            service_id = trip_id

            trips.append({
                "route_id": route_id,
                "service_id": service_id,
                "trip_id": trip_id,
                "trip_headsign": trip_detail.direction,
            })

            dates_for_trip = data.trip_calendar.get(trip_id, set())
            for date in dates_for_trip:
                calendar_dates.append({
                    "service_id": service_id,
                    "date": date,
                    "exception_type": 1,
                })

            last_departure_seconds = -1
            for idx, stop_time in enumerate(trip_detail.times):
                place_id = stop_time.get("place_id", "")
                if ":" in place_id:
                    stop_id = place_id.split(":", 1)[1]
                else:
                    stop_id = place_id
                departure_seconds = time_to_seconds(stop_time["departure_time"])
                if departure_seconds < last_departure_seconds:
                    departure_seconds += 24 * 3600
                last_departure_seconds = departure_seconds
                stop_times.append({
                    "trip_id": trip_id,
                    "arrival_time": seconds_to_time(departure_seconds),
                    "departure_time": seconds_to_time(departure_seconds),
                    "stop_id": stop_id,
                    "stop_sequence": idx + 1,
                })

        for route_key, route_record in routes.items():
            lookup_key = (route_key, data.provider.prefix.lower())
            if lookup_key in vehicle_settings:
                route_record["route_type"] = vehicle_settings[lookup_key]

        if routes:
            zf.writestr("routes.txt", csv_string(list(routes.values()), list(next(iter(routes.values())).keys())))
        if trips:
            zf.writestr("trips.txt", csv_string(trips, trips[0].keys()))
        if stop_times:
            zf.writestr("stop_times.txt", csv_string(stop_times, stop_times[0].keys()))
        if calendar_dates:
            zf.writestr("calendar_dates.txt", csv_string(calendar_dates, calendar_dates[0].keys()))

    print(f"GTFS generation finished: {file_name}")