import osm_tags
import output
import utility as uti
import metadata
import country_detection
import gpxpy
import pandas as pd
import argparse
from termcolor import colored

# ------------------------------------------------------------
# INIT
# ------------------------------------------------------------


def setup_parser():
    parser = argparse.ArgumentParser(
        description='Finds stuff next to your route.')

    # input file
    parser.add_argument('-f',
                        '--input-file',
                        metavar='route.gpx',
                        required=True,
                        type=str,
                        nargs='?',
                        help='used to supply your gpx file',
                        dest="input-file")

    # search distance
    parser.add_argument(
        '-d',
        '--search-distance',
        metavar='<distance>',
        required=False,
        type=float,
        nargs='?',
        help=
        "defines approx. search radius around route in kilometers (default=1km)",
        dest="search-distance",
        default=1)

    # list of countries
    parser.add_argument(
        '-c',
        '--country-codes',
        metavar='countries',
        default="AUTO",
        required=False,
        type=str,
        nargs='?',
        help=
        "comma separated list of country codes (ISO 3166-1 Alpha-2 --> see Wikipedia), e.g., DE,US,FR (default=AUTO --> autodetection)",
        dest="country-codes")

    # use cache or not
    parser.add_argument(
        '-r',
        '--redownload-files',
        action='store_true',
        required=False,
        help="""if you want to redownload the large file from the openstreetmap
        repository. This does not include processing of the file. Regardless of
        this option files will be downloaded automatically if they do not
        exist.""",
        dest="redownload-files")

    # use cache or not
    parser.add_argument(
        '-m',
        '--reprocess-files',
        action='store_true',
        required=False,
        help=
        """if you wat to reprocess the large openstreetmap file into the metadata
        file that is used for finding points of interest. Regardless of this
        option files will be processed automatically if the processed file does not exist.""",
        dest="reprocess-files")

    # set output mode
    parser.add_argument(
        '-o',
        '--output-modes',
        required=False,
        metavar="print|csv|google-sheets|pdf|html-map",
        type=str,
        default="csv,print,html-map",
        help=
        "comma separated list of output modes, e.g., print,csv (default=csv,print,html-map)",
        dest="output-modes")

    # choose points of interest
    parser.add_argument(
        '-p',
        '--points-of-interest',
        required=False,
        metavar="|".join(osm_tags.get_osm_tag_mapping()
                         ["route-report-group"].drop_duplicates().to_list()),
        default="food-shop,water,petrol-station",
        type=str,
        help=
        """comma separated list of points-of-interest the program is supposed to
        look for along the route (default=food-shop,water,petrol-station)""",
        dest="points-of-interest")

    return vars(parser.parse_args())


# ------------------------------------------------------------
# FILE INTERACTIONS
# ------------------------------------------------------------


def extract_points(filename):
    gpx_file = open(filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    all_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                all_points.append({
                    "latitude": point.latitude,
                    "longitude": point.longitude
                })

    route = pd.DataFrame(all_points)
    # compute distances between points to get about the position/kilometer on
    # the route where the point is
    route["lat_next"] = route["latitude"].shift(1)
    route["long_next"] = route["longitude"].shift(1)
    route["diff_distance"] = route.apply(uti.metric_distance_between_latlong,
                                         args=("latitude", "longitude",
                                               "lat_next", "long_next"),
                                         axis=1)
    route["cum_distance_km"] = route["diff_distance"].cumsum().apply(int)

    return route[["latitude", "longitude", "cum_distance_km"]]


# ------------------------------------------------------------
# MAIN STUFF
# ------------------------------------------------------------


def get_poi(ser):
    """gets points of interested around a given point (lat, long)"""
    # TODO performance?
    # TODO make nice and less hacky
    lati = ser["latitude"]
    long = ser["longitude"]
    subset = poi[((poi["longitude"] - long).abs() < search_distance)
                 & ((poi["latitude"] - lati).abs() < search_distance)]
    list_of_poi = [(row[1]["id"], row[1]["name"], row[1]["latitude"],
                    row[1]["longitude"], row[1]["poi_groups"])
                   for row in subset.iterrows()]
    return list_of_poi


def postprocess_route_results(route):
    # TODO remove duplicates by distance to each other --> check if there are
    # duplicate supermarkets --> saved as way and node

    # remove points without poi
    route = route[route["poi"].apply(len) != 0]

    # first get one pois per line
    route = route.explode("poi")

    # extract data for pois
    route["poi_id"] = route["poi"].str[0]
    route["poi_name"] = route["poi"].str[1]
    route["poi_lat"] = route["poi"].str[2]
    route["poi_long"] = route["poi"].str[3]
    route["poi_groups"] = route["poi"].str[4]
    del route["poi"]

    # compute distance between route point and poi
    route["poi_distance_to_route"] = route.apply(
        uti.metric_distance_between_latlong,
        args=["latitude", "longitude", "poi_lat", "poi_long"],
        axis=1)

    # if poi is listed multiple times, then keep the one with the closest
    # distance to route
    route = route.sort_values(by="poi_distance_to_route")
    route = route.drop_duplicates(subset=["poi_id"], keep="first")

    # sort list by cum. km and pois name
    route = route.sort_values(by=["cum_distance_km", "poi_name"])
    return route


def main(args):
    global search_distance
    if args["search-distance"] is None:
        uti.log(
            colored(
                "If you use the -d option you also need to supply a distance!",
                "red"))
        exit()
    search_distance = uti.convert_km_to_latlong(args["search-distance"])

    # processing the gpx file
    uti.log("reading and preprocessing route...", expect_more=True)
    route = extract_points(args["input-file"])
    orignal_route = route.copy(deep=True)
    uti.log("DONE", append=True)

    # detecting countries on route
    if args["country-codes"] == "AUTO":
        uti.log("detecting countries on route...", expect_more=True)
        country_codes = country_detection.detect_country_for_points(
            route[["latitude", "longitude"]])
        uti.log(",".join(country_codes) + "...", append=True, expect_more=True)
        uti.log("DONE", append=True)
    else:
        country_codes = args["country-codes"].split(',')

    # downlaod metadata files if necessary
    metadata.download_and_preprocess_metadata(country_codes,
                                              args["redownload-files"],
                                              args["reprocess-files"])

    # read in metadata
    uti.log("reading metadata...", expect_more=True)
    global poi
    poi = metadata.read_metadata(country_codes)
    # only take poi the user wants
    points_of_interest_group_filter = set(
        args["points-of-interest"].split(','))
    poi = poi[poi["poi_groups"].apply(lambda groups: any(
        [group in points_of_interest_group_filter for group in groups]))]
    uti.log("DONE", append=True)

    # get the poi
    uti.log("searching for points of interest...", expect_more=True)
    route["poi"] = route.apply(get_poi, axis=1)

    # the approach below using polygons is only twice as fast and still requires postprocessing and matching with route
    # create route and add search distance area around it
    # route_polygon = LineString(map(Point,zip(route["latitude"], route["longitude"]))).buffer(search_distance)
    # filter poi that are in polygon
    # poi = poi[poi[["latitude", "longitude"]].apply(lambda point: route_polygon.contains(Point(tuple(point))), axis=1)]

    route = postprocess_route_results(route)
    uti.log("DONE", append=True)

    return route, orignal_route


if __name__ == "__main__":
    args = setup_parser()
    route_with_shops, orignal_route = main(args)
    output.output_results(route_with_shops,
                          orignal_route,
                          modes=args["output-modes"].split(','),
                          original_filename=args["input-file"].replace(
                              ".gpx", "").split('/')[-1])
