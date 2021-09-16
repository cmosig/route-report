import pandas as pd


def get_osm_tag_mapping():
    # take left column from osm_tag file
    return pd.read_csv("./other_data/osm_tags.csv", sep="|", dtype=str)
