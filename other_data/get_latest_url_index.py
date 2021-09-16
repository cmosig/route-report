import urllib.request, json
import pandas as pd

with urllib.request.urlopen(
        "https://download.geofabrik.de/index-v1.json") as url:
    data = json.loads(url.read().decode())
    mapping = dict()
    for feature in data["features"]:
        try:
            iso = tuple(feature["properties"]["iso3166-1:alpha2"])
            if len(iso) > 1:
                continue
            else:
                iso = iso[0]
        except:
            continue
        mapping[feature["properties"]["id"]] = [
            iso, feature["properties"]["urls"]["pbf"]
        ]
    
    df = pd.DataFrame.from_dict(mapping, orient="index")
    df.columns = ["iso", "url"]
    df = df.dropna()

    df.to_csv("country_code_mapping.csv", index=False)
