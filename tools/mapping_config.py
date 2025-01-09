mapper = "map" # "map" or "mapbox""
defaults = {
    "lat" : "latitude",
    "lon" : "longitude",
    f"{mapper}_style" : "open-street-map",
    "zoom" : 2.7,
    "center" : {"lat":40,"lon":-96},
    }
network = {
    "powerflow" : {
        "ref":("bustype","SWING"),
        "nodes":["from","to"],
        },
    "pypower" : {
        "ref":("type","3"),
        "nodes":["fbus","tbus"],
        },
    }
violation_color = {
    "NONE" : (0,0,0),
    "THERMAL" : (1,0,0),
    "CURRENT" : (0.5,0,0),
    "POWER" : (0,1,0),
    "VOLTAGE" : (0,0,1),
    "CONTROL" : (0,0,0.5),
    }
node_options = {
    "textposition" : "top right",
    # Slows mapping down alot and doesn't display links
    # "cluster" : {
    #     "enabled" : False,
    #     "maxzoom" : 12,"
    # }
    }
