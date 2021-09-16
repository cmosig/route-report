import pandas as pd
import time
from shapely.geometry import Polygon
import esy.osm.pbf
from subprocess import Popen
import requests
import os
from tqdm import tqdm
import osm_tags


def read_metadata(country_codes):
    return_df = pd.concat([
        pd.read_csv(f"country_metadata/{c}-metadata.csv.gz",
                    converters={"poi_groups": eval}) for c in country_codes
    ])
    return return_df


def download_and_preprocess_metadata(country_codes, redownload, reprocess, cleanup=False):
    # load index
    mapping = pd.read_csv("other_data/country_code_mapping.csv",
                          squeeze=True,
                          index_col="iso").to_dict()

    # create country metadata dir
    dir_name = "country_metadata"
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    osm_mapping = osm_tags.get_osm_tag_mapping()

    # other data-structures that are needed later on
    osm_dict = osm_mapping.set_index("osm_tag")["route-report-group"].to_dict()
    all_osm_tags = set(osm_mapping["osm_tag"])

    # convert the osm-tags that are requested into a string that osmosis can read
    osm_mapping[["primary",
                 "secondary"]] = osm_mapping["osm_tag"].str.split("=",
                                                                  expand=True)
    osm_mapping = osm_mapping.groupby("primary")["secondary"].apply(
        lambda x: ",".join(x.drop_duplicates())).reset_index()
    osm_mapping[
        "merged"] = osm_mapping["primary"] + "=" + osm_mapping["secondary"]
    osmosis_string = " ".join(osm_mapping["merged"])

    def get_poi_group(row):
        # TODO can this function be faster?

        # find osm_tags that we are interested in
        tags = set([i + "=" + j for i, j in zip(index, row)])
        osm_tags_in_common = list(tags.intersection(all_osm_tags))
        # translate osm_tag to group and drop dupes
        poi_groups = list(
            set([osm_dict[osm_tag] for osm_tag in osm_tags_in_common]))

        # sanity checks
        assert len(poi_groups) > 0, "could not find poi group"

        # we assume there is only one matching (see above)
        return tuple(poi_groups)

    for code in tqdm(country_codes,
                     desc="Checking country metadata",
                     leave=False):

        fname = f"{dir_name}/{code}-metadata-unfiltered.osm.pbf"
        filter_fname = f"{dir_name}/{code}-metadata.osm.pbf"
        filter_fname_csv = f"{dir_name}/{code}-metadata.csv.gz"

        # get URL for county code
        url = mapping[code]

        # ------------------------------------------------------------
        # 1) Download complete file
        # ------------------------------------------------------------
        # download file
        # progress bar adopted from https://stackoverflow.com/a/62113293/8832008
        # if next file not there or redownload
        if not os.path.exists(filter_fname_csv) or redownload or (
                not os.path.exists(filter_fname) and reprocess):
            resp = requests.get(url, stream=True)
            total = int(resp.headers.get('content-length', 0))
            with open(fname, 'wb') as file, tqdm(desc=f"Downloading {code}",
                                                 total=total,
                                                 unit='iB',
                                                 unit_scale=True,
                                                 unit_divisor=1024,
                                                 leave=False) as bar:
                for data in resp.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)

        # ------------------------------------------------------------
        # 2) Filter osm file by our tags and save using country code
        # ------------------------------------------------------------
        # TODO maybe try to skip osmosis and do filtering with pandas
        if not os.path.exists(filter_fname) or reprocess:

            # TODO add progress bar for this

            # first, we look for ways and then the nodes that define the way/area using --used-node
            # next, we look for nodes that match our filter
            # third, we merge both and save
            # (the remove new line part is only there so that we can use new
            # lines. the shell does not like new lines)
            osmosis_string = f"""osmosis 
            --read-pbf-fast country_metadata/{code}-metadata-unfiltered.osm.pbf workers=8
                --tf accept-ways {osmosis_string}
                --tf reject-relations 
                --used-node 
            --read-pbf-fast country_metadata/{code}-metadata-unfiltered.osm.pbf workers=8
                --tf accept-nodes {osmosis_string}
                --tf reject-relations 
                --tf reject-ways 
            --merge 
            --write-pbf country_metadata/{code}-metadata.osm.pbf 
            2> /dev/null""".replace("\n", "")
            # launch osmosis process and wait until its done
            Popen(osmosis_string, shell=True).wait()

            # ------------------------------------------------------------
            # 3) Convert to CSV and get poi-groups
            # ------------------------------------------------------------
            # read poi file and process --> then save as csv
            # ------------------------------------------------------------
            osm = esy.osm.pbf.File(filter_fname)

            # assumption that does not hold: nodes without tags are waypoints for ways

            # first get waypoint IDs
            waypoint_ids = []
            for item in osm:
                if isinstance(item, esy.osm.pbf.Way):
                    waypoint_ids += item.refs
            waypoint_ids = set(waypoint_ids)

            # then extract waypoints
            waypoints = dict()
            for item in osm:
                if item.id in waypoint_ids and isinstance(
                        item, esy.osm.pbf.Node):
                    # ID -> (lon,lat)
                    waypoints[item.id] = item.lonlat

            tags = []
            lonlat = []
            ids = []
            # get nodes and waypoints
            for item in osm:
                # skip waypoints
                if item.id in waypoint_ids:
                    continue

                # if we have nodes simply add them to list
                if isinstance(item, esy.osm.pbf.Node):
                    tags.append(item.tags)
                    lonlat.append(item.lonlat)
                    ids.append(item.id)

                # if we have ways then get way points and compute center
                if isinstance(item, esy.osm.pbf.Way):
                    # polygon needs at least 3 points
                    if len(item.refs) >= 3:
                        center = Polygon([
                            waypoints[waypointid] for waypointid in item.refs
                        ]).centroid
                        lonlat.append((center.x, center.y))
                    else:
                        # just taking the first waypoint if there is less than 3
                        lonlat.append(waypoints[item.refs[0]])
                    tags.append(item.tags)
                    ids.append(item.id)

            poi = pd.DataFrame.from_dict(tags)

            index = list(poi.columns)
            poi = poi.fillna("")
            poi["poi_groups"] = poi.apply(get_poi_group, axis=1)
            poi["lonlat"] = lonlat
            poi["id"] = ids
            poi["longitude"] = poi["lonlat"].str[0]
            poi["latitude"] = poi["lonlat"].str[1]
            poi[["id", "name", "longitude", "latitude",
                 "poi_groups"]].to_csv(filter_fname_csv,
                                       compression="gzip",
                                       index=False)

            if cleanup:
                os.remove(fname)
                os.remove(filter_fname)
