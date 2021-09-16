# Route-Report

Route report is a command-line utility that can be used to locate
points-of-interest near your planned route (gpx). The results are based on the
database by OpenStreetMap.

If the metadata for the requested countries is not present then Route-Report
first downloads [OpenStreetMap](https://www.openstreetmap.org) metadata. Then, we use
[`osmosis`](https://wiki.openstreetmap.org/wiki/Osmosis) in the background to
filter through the metadata and extract relevant locations. This has to be done
only once for each country you want to use and the resulting, filtered file is
quite small (<1MB for Germany). If you want to retrieve an up-to-date version
of the files you can use the `-r` flag.

**Note that the metadata files in this repo are only as up-to-date as their
change date. You may want to download more recent files (`-r` flag).
Supermarkets don't move often though :P**

## Usage 

```
usage: route_report.py [-h] -f [route.gpx] [-d <distance>] [-c [countries]] [-r] [-m] [-o print|csv|google-sheets|pdf|1D-map]
                       [-p food-shop|petrol-station|water]

Finds stuff next to your route.

optional arguments:
  -h, --help            show this help message and exit
  -f [route.gpx], --input-file [route.gpx]
                        used to supply your gpx file
  -d <distance>, --search-distance <distance>
                        defines approx. search radius around route in kilometers (default=1km)
  -c [countries], --country-codes [countries]
                        comma separated list of country codes (ISO 3166-1 Alpha-2 --> see Wikipedia), e.g., DE,US,FR (default=AUTO --> autodetection)
  -r, --redownload-files
                        if you want to redownload the large file from the openstreetmap repository. This does not include processing of the file. Regardless
                        of this option files will be downloaded automatically if they do not exist.
  -m, --reprocess-files
                        if you wat to reprocess the large openstreetmap file into the metadata file that is used for finding points of interest. Regardless
                        of this option files will be processed automatically if the processed file does not exist.
  -o print|csv|google-sheets|pdf|1D-map, --output-modes print|csv|google-sheets|pdf|1D-map
                        comma separated list of output modes, e.g., print,csv (default=print)
  -p food-shop|petrol-station|water, --points-of-interest food-shop|petrol-station|water
                        comma separated list of points-of-interest the program is supposed to look for along the route (default=food-shop)
```

## Points of Interest

Poi-groups are a collection of OpenStreetMap (OSM) tags are grouped together in
our program. For example the poi-group `food-shop` represents convenience
stores, grocery stores, bakeries, etc.
The right column in the file `./other_data/osm_tags.csv` shows you poi-groups
you can search for along your route using the `-p` flag (see Example). The left
column in that file represents all OSM tags that we search for given a specific
poi-group(s). 

You can change `./other_data/osm_tags.csv` however you like, just be aware that
the metadata files in this repository only contain locations with the tags we
are using. If you wish to use your own tags you can refresh your metadata files
using the `-r` flag after you have changed `./other_data/osm_tags.csv`.

## Autodetection of countries

We autodetect countries based on the gpx file you provide using
the [thematicmapping](http://thematicmapping.org/downloads/world_borders.php)
dataset. If you wish to use only a subset of country datasets you can specify
them using the `-c` flag. 

Autodetection of countries takes about 30s (on my laptop) for a 1000km route.
This will take even longer for longer routes. Therefore, I suggest you directly
specify countries with the `-c` if computing resources are scarce.

## Example

By default, you can just supply a gpx-file with the `-f` option and the program
will take care of the rest. For illustration, the below example is more complex. 

Assuming you have route planned on [Komoot](https://www.komoot.com/discover)
and you want to know about `food-shop` and `petrol-station` (`-p`) next to your
route that are within 2km (`-d`) you can download the gpx file and then run the
command below. Additionally, you would like the program to print the output to
stdout (`-o print`) and create a html map with the results (`-o html-map`)

```
>>> python3 route_report.py -f gpx_test_files/test_route_andorra.gpx -p food-shop,petrol-station -d 2 -o print,html-map

     cum_distance_km                      poi_name  poi_distance_to_route    poi_lat  poi_long       poi_group
20                 0                   Consciència               0.085418  42.508222  1.520737       food-shop
11                 0               Eco Supermacats               0.474783  42.505049  1.514742       food-shop
22                 0                    Fleca Font               0.006591  42.507441  1.521643       food-shop
30                 0                           NaN               0.118936  42.506687  1.523430       food-shop
5                  0                           NaN               0.658057  42.501832  1.515404       food-shop
59                 1                  Andorra 2000               0.320416  42.505714  1.529197       food-shop
89                 1               Biocoop Andorra               0.225353  42.508006  1.537685       food-shop
81                 1                       Caprabo               0.133882  42.508700  1.534714       food-shop
66                 1                    E. Leclerc               0.070915  42.508874  1.532163       food-shop
92                 1                    Fleca font               0.088633  42.509274  1.538085       food-shop
73                 1                  Santa Glòria               0.187045  42.508125  1.533945       food-shop
60                 1                       Super U               0.088410  42.507963  1.530428       food-shop
59                 1             bonÀrea (Andorra)               0.260034  42.506250  1.529328       food-shop
59                 1                    de bon Gra               0.157387  42.507171  1.529441       food-shop
60                 1                           NaN               0.070890  42.508139  1.530399       food-shop
113                2                  13-th street               0.013526  42.509196  1.540867       food-shop
115                2                         Artal               0.107198  42.508185  1.539805  petrol-station
145                2                       Artal 2               0.121834  42.510551  1.548264  petrol-station
130                2                        Repsol               0.103972  42.508329  1.545053  petrol-station
126                2                           NaN               0.006941  42.509005  1.543588       food-shop
208                4                            BP               0.018608  42.522095  1.559524  petrol-station
207                4                         Cepsa               0.024718  42.521652  1.559482  petrol-station
248                6                         Cepsa               0.020690  42.531754  1.577210  petrol-station
251                6           Comer la Clementina               0.171664  42.533281  1.579239       food-shop
292                7                            BP               0.011910  42.536710  1.589220  petrol-station
273                7                            BP               0.021828  42.533517  1.585820  petrol-station
292                7               Comerç les Bons               0.234051  42.537693  1.586538       food-shop
267                7                           ECO               0.387443  42.536011  1.582085       food-shop
266                7                        Repsol               0.037308  42.533489  1.584708  petrol-station
267                7                           NaN               0.388133  42.536065  1.582158       food-shop
305                8  Avenida Doctor Mitjavila, 3-               0.643809  42.542483  1.599984       food-shop
310                8                          Esso               0.019175  42.542198  1.591422  petrol-station
433               11                       Caprabo               0.016012  42.566131  1.598642       food-shop
434               11        Les delícies del Jimmy               0.026433  42.566201  1.598758       food-shop
451               11                         Total               0.031216  42.566991  1.600830  petrol-station
536               15                            BP               0.513669  42.579580  1.640062  petrol-station
```

Ignore the leftmost column. The column `cum_distance_km` represents
the point of the route where the grocery store has been found and the column
`shop_distance_to_route` represents how far away the shop is from the route in
kilometers. For example, after riding this route for 11 kilometers you will
encounter a Caprabo (food-shop) 16m next to the route.

## Future Work

The filtering part (with `osmosis`) only works on Linux for now. I plan on
supplying either already filtered files for each country or some alternative
that works on Windows/Mac in the future. Note that the rest of the program
should still work on other platforms.

There are many minor touches missing, e.g., a nicer output, creating an
executable, custom alerts, or supporting the imperial system.
