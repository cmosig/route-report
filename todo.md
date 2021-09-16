# TODO critical / do asap 

* output files should not have a generic name but some version of the gpx file
  name
* make readme markdown page readable and update with essential stuff

# TODO do soon / kinda essential to have

* display max N entries per kilometer
* add opening times
* add default icons for POI new poi groups / make configurable in the existing
  table file
* add progress bar for file processing / osmosis processing (it is possible to
  track progress with the --lp option, but it only seems to report how many
  items have been processed, not how many items are left) (another option is to
  push the raw stream through pv; there were some issues, too lazy to debug)

# TODO nice to have

* validate user input and give nice error messages instead of letting the whole
  thing crash
* handle no gpx files, i.e., option to downloading and processing just country
  data without needing to supply a route
* build small interface --> import gpx --> set options --> open browser
* support imperial --> add mode
* add notifications about important results such as: distance between consecutive shops >100
* add argument where users can supply the metadata file(s) themselves

# TODO unspecific 

* work on other output modes
* optimize
* add tests and stuff

# TODO wtf were you thinking when writing this???

* create binary with libs included
* come up with solution for Mac/Windows
