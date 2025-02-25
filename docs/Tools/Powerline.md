[[/Tools/Powerline]] -- Powerline data tool

Syntax: `gridlabd powerline COUNTRY [STATE [COUNTY]] [OPTIONS ...]

Options:

* `-o|--output=FILENAME`: output network model to FILENAME

* `--verify={syntax,solve}`: verify the model before saving

* `--reference=BUS`: specify the reference bus to start from (only connected
  nodes will be included)

Description:

The `powerline` tool reads the HIFLD transmission line data repository and
generates a network model for the specified region.  The output FILENAME may
a `.glm` or `.json` file.  If the `--verify=syntax` option is included, the
generated model is loaded in GridLAB-D using the compile option. If the
`--verify=solve` option is included, the network powerflow is solve for
initial conditions.

Example:

See also:

* [[/Tools/Powerplant]]
* [HIFLD transmission line data repository](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::transmission-lines/about)



# Constants

* `CONVERTERS`

# Modules

* `geojson`
* `gridlabd.framework`
* `gridlabd.resource`
* `gzip`
* `io`
* `os`
* `pandas`
* `random`
* `requests`
* `sys`
