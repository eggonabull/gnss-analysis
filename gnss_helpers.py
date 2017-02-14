#!/usr/bin/env python
import csv
import latlon
import matplotlib.pyplot as plt

from haversine import haversine
from dateutil.parser import parse as parse_date
from ipyleaflet import Map, Polyline


class LatLngTime():
    def __init__(self, lat_string, lon_string, time):
        lat = float(lat_string)
        lon = float(lon_string)
        self.lat = lat
        self.lon = lon
        self.time = time
        self.latlon = [lat, lon]

    def __getitem__(self, item):
        return self.latlon[item]

    def __len__(self):
        return 2

    def __str__(self):
        return "LatLngTime(%f, %f, %s)" % (self.lat, self.lon, self.time)


def get_data(datafile):
    latlngs = []
    with open(datafile, 'r') as csvfile:
        csvfile.readline()  # skip header
        csv_iterator = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in csv_iterator:
            annotated_latlng = LatLngTime(
                row[2],
                row[1],
                parse_date(row[0])
            )
            latlngs.append(annotated_latlng)
    return latlngs


def get_bounds_for_linestring(linestring):
    # print("typeof(linestring)", type(linestring))
    # print("linestring", linestring)
    min_lat = 90
    max_lat = -90
    min_lon = 180
    max_lon = -180
    for point in linestring:
        lat = point[0]
        lon = point[1]
        if lat < min_lat:
            min_lat = lat
        if lat > max_lat:
            max_lat = lat
        if lon < min_lon:
            min_lon = lon
        if lon > max_lon:
            max_lon = lon
    return {
        "min_lat": min_lat,
        "min_lon": min_lon,
        "max_lat": max_lat,
        "max_lon": max_lon
    }


def get_map_for_linestring(linestring, zoom=14):
    bounds = get_bounds_for_linestring(linestring)
    center_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2
    center_lon = (bounds["min_lon"] + bounds["max_lon"]) / 2
    center = [center_lat, center_lon]
    p = Polyline(locations=[ll.latlon for ll in linestring], color='red', fill=False)
    m = Map(center=center, zoom=zoom)
    m += p
    return m


def get_map_for_data_file(datafile, zoom=14):
    data = get_data(datafile)
    return get_map_for_linestring(data, zoom)


def get_velocity_data(data):
    prev_point = data[0]
    results = []
    for point in data[1:]:
        diff_vec = latlon.diff(prev_point, point)
        unit_vec = latlon.unit(diff_vec)
        distance = haversine(point, prev_point, miles=True)
        tdiff_hours = (point.time - prev_point.time).total_seconds() / 60 / 60
        if tdiff_hours == 0:
            prev_point = point
            continue
        speed_vec = latlon.scale(unit_vec, distance / tdiff_hours)
        mid_time = point.time - (point.time - prev_point.time) / 2
        prev_point = point
        results.append(LatLngTime(speed_vec[0], speed_vec[1], mid_time))

    return results


def get_velocity_plot(datafile):
    data = get_data(datafile)
    velocity_data = get_velocity_data(data)
    x, y = zip(*velocity_data)
    plt.scatter(x, y, color=(0.1, 0.3, 0.6, 0.1))
    return plt.show()


def get_acceleration_plot(datafile):
    data = get_data(datafile)
    velocity_data = get_velocity_data(data)
    results = []
    for i in range(1, len(velocity_data)):
        prev_v = velocity_data[i - 1]
        v = velocity_data[i]
        diff_vec = latlon.diff(prev_v, v)
        tdiff = (v.time - prev_v.time).total_seconds()
        acc_vec = latlon.scale(diff_vec, 1 / tdiff)
        results.append(acc_vec)
    x, y = zip(*results)
    plt.scatter(x, y, color=(0.4, 0.6, 0.1, 0.1))
    return plt.show()
