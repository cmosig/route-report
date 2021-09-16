import utility as uti
import os
import webbrowser
import pandas as pd
from termcolor import colored
import folium
from shapely.geometry import Polygon


def _determine_route_center(route):
    return tuple(
        Polygon(list(zip(route["latitude"],
                         route["longitude"]))).centroid.coords)[0]


def _create_html_map(route_with_shops, original_route, original_filename, gui):
    # init map on center of route
    html_map = folium.Map(location=_determine_route_center(original_route))

    # add route to map
    folium.vector_layers.PolyLine(
        zip(original_route["latitude"],
            original_route["longitude"])).add_to(html_map)

    # show poi on map
    for _, row in route_with_shops.iterrows():
        # select icon type --> maybe move into config file
        if "food-shop" in row["poi_groups"]:
            icon_args = {
                "color": "red",
                "icon": "shopping-cart",
                "prefix": "fa"
            }
        elif "water" in row["poi_groups"]:
            icon_args = {"color": "blue", "icon": "glyphicon-tint"}
        elif "petrol-station" in row["poi_groups"]:
            icon_args = {"color": "gray", "icon": "wrench", "prefix": "fa"}

        # place marker on map
        folium.Marker(location=(row["poi_lat"], row["poi_long"]),
                      popup=folium.Popup(
                          f"""{row['poi_name']} ({','.join(row['poi_groups'])})
                | Kilometer: {row['cum_distance_km']}
                """,
                          max_width="500",
                      ),
                      icon=folium.map.Icon(**icon_args)).add_to(html_map)

    # save to html
    fname = f"{original_filename}.html"
    html_map.save(f"{original_filename}.html")
    if gui:
        webbrowser.open_new_tab(f"{original_filename}.html")


def output_results(route_with_shops, original_route, modes, original_filename="result", gui=True):
    # possible modes: print, google-sheets, 1D-map, csv, pdf, html-map
    # THIS IS A BIG TODO
    if "print" in modes:
        print(route_with_shops[[
            "cum_distance_km", "poi_name", "poi_distance_to_route", "poi_lat",
            "poi_long", "poi_groups"
        ]].to_string())
    if "google-sheets" in modes:
        uti.log(
            colored("google-sheets output mode is currently not supported",
                    "red"))
        pass
    if "1D-map" in modes:
        uti.log(colored("1D-map output mode is currently not supported",
                        "red"))
        pass
    if "csv" in modes:
        route_with_shops.to_csv(f"{original_filename}.csv", index=False)
        # uti.log(colored("csv output mode is currently not supported", "red"))
        # pass
    if "pdf" in modes:
        uti.log(colored("pdf output mode is currently not supported", "red"))
        pass
    if "html-map" in modes:
        _create_html_map(route_with_shops, original_route, original_filename, gui)

    # add google link based on latlong of shop
    # route["google_link"] = route["shop"].apply(
    #     lambda tup:
    #     f"https://www.google.com/maps/search/?api=1&query={tup[1]},{tup[2]}")
    # pd.set_option('display.max_colwidth', None)


if __name__ == "__main__":
    route = pd.read_pickle("test_route.pkl")
    original_route = pd.read_pickle("original_test_route.pkl")
    _create_html_map(route, original_route)
