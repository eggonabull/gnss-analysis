#!/usr/bin/env python
import csv
import latlon
import math
import matplotlib.pyplot as plt

import matplotlib
from matplotlib import collections as mc

from haversine import haversine
from dateutil.parser import parse as parse_date
from ipyleaflet import Map, Polyline, Marker


class LatLngTime():
    def __init__(self, lat_string, lon_string, time):
        lat = float(lat_string)
        lon = float(lon_string)
        self.lat = lat
        self.lon = lon
        self.time = time
        self.latlon = [lat, lon]
        self.acc = None
        self.prev_speed = None
        self.next_speed = None
        self.angular_velocity = None

    def __getitem__(self, item):
        return self.latlon[item]

    def __len__(self):
        return 2

    def __str__(self):
        return "LatLngTime(%f, %f, %s)" % (self.lat, self.lon, self.time)

    def __repr__(self):
        return self.__str__()


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


def get_annotated_data(datafile):
    latlngs = get_data(datafile)
    num_latlngs = len(latlngs)
    for i in range(1, num_latlngs):
        #print(latlngs[i - 1], latlngs[1])
        speed_vec = get_velocity_vector(latlngs[i - 1], latlngs[i])
        latlngs[i - 1].next_speed = speed_vec
        latlngs[i].prev_speed = speed_vec

        if i > 1 and latlngs[i - 1].next_speed is not None and latlngs[i - 1].prev_speed is not None:
            speed_diff_vec = latlon.diff(latlngs[i - 1].next_speed, latlngs[i - 1].prev_speed)
            tdiff_speed = (latlngs[i - 1].next_speed.time - latlngs[i - 1].prev_speed.time).total_seconds()
            acc_vec = latlon.scale(speed_diff_vec, 1 / (tdiff_speed))
            latlngs[i - 1].acc = acc_vec
        else:
            latlngs[i - 1].acc = None
    return latlngs


def get_bounds_for_linestring(linestring):
    return get_bounds_for_linestrings([linestring])


def get_bounds_for_linestrings(linestrings):
    # print("typeof(linestring)", type(linestring))
    # print("linestring", linestring)
    min_lat = 90
    max_lat = -90
    min_lon = 180
    max_lon = -180
    for linestring in linestrings:
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
    return get_map_for_linestrings([linestring], zoom)


def get_map_for_linestrings(linestrings, zoom=14):
    bounds = get_bounds_for_linestrings(linestrings)
    center_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2
    center_lon = (bounds["min_lon"] + bounds["max_lon"]) / 2
    center = [center_lat, center_lon]
    m = Map(center=center, zoom=zoom)
    max_len = 0
    for linestring in linestrings:
        max_len = max(max_len, len(linestring))
    for linestring in linestrings:
        # intensity = 1 - len(linestring) / max_len
        # color = "#" + ("{:02x}".format(round(intensity * 255)) * 3)
        p = Polyline(locations=[point.latlon for point in linestring], fill=False)
        m += p
    return m

import pylab as pl

def get_plot_for_linestrings(linestrings, zoom=14):
    bounds = get_bounds_for_linestrings(linestrings)
    center_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2
    center_lon = (bounds["min_lon"] + bounds["max_lon"]) / 2
    center = [center_lat, center_lon]
    max_len = 0
    colors = []
    lines = []
    outputs = []
    for linestring in linestrings:
        max_len = max(max_len, len(linestring))
    for linestring in linestrings:
        for i in range(1, len(linestring)):
            #intensity = 1 - len(linestring) / max_len
            #color = "#" + ("{:02x}".format(round(intensity * 255)) * 3)
            point = linestring[i]
            prev_point = linestring[i - 1]
            angular_velocity = point.angular_velocity
            hue = angular_velocity / 14 if angular_velocity is not None else 0
            lightness = 1 if angular_velocity is not None else 0
            color = matplotlib.colors.hsv_to_rgb((hue, 1, lightness))
            outputs.append(([prev_point.latlon, point.latlon], color))
    outputs = sorted(outputs, key=lambda x: 1-x[1][0])
    lines = [output[0] for output in outputs]
    colors = [output[1] for output in outputs]
    lc = mc.LineCollection(lines, colors=colors, linewidths=2)
    fig, ax = pl.subplots()
    ax.add_collection(lc)
    ax.autoscale()
    ax.margins(0.1)
    return plt.show()


def get_map_for_data_file(datafile, zoom=14):
    data = get_data(datafile)
    return get_map_for_linestring(data, zoom)


def get_velocity_vector(prev_point, point):
    diff_vec = latlon.diff(prev_point, point)
    unit_vec = latlon.unit(diff_vec)
    distance = haversine(point, prev_point, miles=True)
    tdiff_hours = (point.time - prev_point.time).total_seconds() / 60 / 60
    if tdiff_hours == 0:
        return None
    speed_vec = latlon.scale(unit_vec, distance / tdiff_hours)
    mid_time = point.time - (point.time - prev_point.time) / 2
    llt = LatLngTime(speed_vec[0], speed_vec[1], mid_time)
    llt.distance = distance
    return llt


def get_velocity_data(data):
    prev_point = data[0]
    results = []
    for point in data[1:]:
        speed_vec = get_velocity_vector(prev_point, point)
        if speed_vec is not None:
            results.append(speed_vec)
        prev_point = point
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


def get_angular_velocity_data(data):
    prev_point = data[0]
    results = []
    for point in data[1:-2]:
        u = point.prev_speed
        v = point.next_speed
        if u is None or v is None:
            continue
        num = u[0]*v[0]+u[1]*v[1]
        denom = latlon.abs(u) * latlon.abs(v)
        if denom == 0:
            continue
        #print("num", num, "denom", denom)
        try:
            angle = math.acos(num/denom)
            angular_velocity = (angle / (v.time - u.time).total_seconds()) * (latlon.abs(u) + latlon.abs(v)) / 2
            results.append(angular_velocity)
            point.angular_velocity = angular_velocity
        except ValueError:
            continue
    return results

def angular_velocity_plot(datafile):
    data = get_annotated_data(datafile)
    angular_velocity = get_angular_velocity_data(data)
    #plt.hist(angular_velocity)
    plt.scatter(range(len(angular_velocity)), sorted(angular_velocity), color="#665500")
    #plt.axis([0, 35000, 0, 90])
    return plt.show()

def angular_velocity_plot_for_data(data):
    angular_velocity = []
    for datum in data:
        angular_velocity += get_angular_velocity_data(datum)
    #plt.hist(angular_velocity)
    plt.scatter(range(len(angular_velocity)), sorted(angular_velocity), color="#665500")
    #plt.axis([0, 35000, 0, 90])
    return plt.show()

