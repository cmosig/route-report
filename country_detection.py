import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point, MultiPolygon, LineString


def detect_country_for_points(points):
    # TODO could optimize such that we only detect country every X kilometers
    # TODO could also create a cache for each gpx file (when we build a webserver)

    country_ser = gpd.read_file(
        "./other_data/tm_world_borders/TM_WORLD_BORDERS-0.3.shp").set_index(
            "ISO2")["geometry"]

    def get_country(route_point):
        nonlocal country_ser
        # move to front algorithm --> prioritize countries that we already found
        # points in
        # NOTE latitude and longitude has to be this way around. dont ask me why...
        p = Point(route_point["longitude"], route_point["latitude"])
        country_to_move = None
        polygon_to_move = None
        is_first = True
        for country_code, polygon in country_ser.items():
            if polygon.contains(p):
                country_to_move = country_code
                polygon_to_move = polygon
                break
            is_first = False

        if country_to_move is None:
            return None
        assert country_to_move is not None and polygon_to_move is not None, "should not happen"

        # move country row to front (more than a 10x speedup)
        if not is_first:
            country_ser = country_ser.drop(country_to_move)
            country_ser = pd.Series(data=[polygon_to_move],
                                    index=[country_to_move
                                           ]).append(country_ser)

        # return ISO country code
        return country_to_move

    unique_country_codes = points.apply(
        get_country, axis=1).dropna().drop_duplicates().to_list()
    return unique_country_codes
