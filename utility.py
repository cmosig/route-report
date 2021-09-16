import pandas as pd
import geopy.distance
from datetime import datetime as dt
import sys


def convert_km_to_latlong(km):
    # NOTE: this is a rough estimate
    return km / 111


def metric_distance_between_latlong(ser, p1_lat, p1_long, p2_lat, p2_long):
    # TODO nicer handling
    try:
        return geopy.distance.distance((ser[p1_lat], ser[p1_long]),
                                       (ser[p2_lat], ser[p2_long])).km
    except:
        return 0


def log(message: str, expect_more=False, append=False):
    if expect_more and not append:
        print(str(dt.now()) + "\t| " + message, end='')
    if expect_more and append:
        print(message, end='')
    if not expect_more and append:
        print(message)
    if not expect_more and not append:
        print(str(dt.now()) + "\t| " + message)
    sys.stdout.flush()
