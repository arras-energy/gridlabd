import marimo

__generated_with = "0.1.66"
app = marimo.App(width="full")


@app.cell
def __(mo):
    mo.md("# GridLAB-D NSRDB Weather")
    return


@app.cell
def __(get_apikey, get_whoami, gridlabd, json, os, set_apikey, set_whoami):
    #
    # NSRDB credentials
    #
    credentials = f"{os.environ['HOME']}/.nsrdb/credentials.json"
    def load_credentials():
        try:
            with open(credentials,"r") as fh:
                whoami,apikey = list(json.load(fh).items())[0]
                set_whoami(whoami)
                set_apikey(apikey)
        except:
            set_whoami(None)
            set_apikey(None)

    def send_registration(_):
        if get_whoami() is None:
            gridlabd("nsrdb_weather",f"--signup={get_whoami()}")

    def save_credentials(_):
        if get_whoami() and get_apikey():
            with open(credentials,"w") as fh:
                json.dump(fh,{get_whoami():get_apikey()})

    load_credentials()
    return (
        credentials,
        load_credentials,
        save_credentials,
        send_registration,
    )


@app.cell
def __(get_fields, mo, setting_graphxaxis, setting_graphyaxis):
    #
    # Plotting options
    #
    xaxis = mo.ui.dropdown(options=get_fields() if get_fields() else [],
                           label="X Axis:",
                           value=setting_graphxaxis.value if get_fields() else None)
    yaxis = mo.ui.multiselect(options=get_fields() if get_fields() else [],
                              label="Y Axis:",
                              value=[setting_graphyaxis.value] if get_fields() else None)
    grid = mo.ui.switch()
    marker = mo.ui.dropdown(label="Marker:",
                            options=["none",".","x","+","o","^","v"],
                            value="none")
    line = mo.ui.dropdown(label="Line:", 
                          options=["none","solid","dotted","dashed","dashdot"],
                          value="solid")
    return grid, line, marker, xaxis, yaxis


@app.cell
def __(
    geolocator,
    get_latitude,
    get_longitude,
    mo,
    set_city,
    set_latitude,
    set_longitude,
):
    #
    # City finder
    #
    def find_city(*args,**kwargs):
        set_city(location.value)
        loc = geolocator.geocode(location.value)
        set_latitude(f"{loc.latitude:.2f}")
        set_longitude(f"{loc.longitude:.2f}")
    try:
        _addr = geolocator.reverse(f"{get_latitude()},{get_longitude()}").raw["address"]
        _city = _addr.get('city','')
    except:
        _city = "Type a city name"

    location = mo.ui.text(label = "Search for location:",
                          placeholder = _city,
                         )  
    return find_city, location


@app.cell
def __(find_city, location, mo):
    #
    # Location lookup
    #
    lookup = mo.ui.button(label = "Find",
                          on_click = find_city,
                         )
    mo.hstack([mo.hstack([location,
                          lookup,
                         ],justify='start'),
               # mo.hstack([download_csv,
               #            download_glm,
               #           ],justify='start'),
              ])
    return lookup,


@app.cell
def __(
    geolocator,
    get_latitude,
    get_longitude,
    interpolation,
    latitude,
    longitude,
    mo,
    preview,
    year,
):
    #
    # Weather location
    #
    try:
        _addr = geolocator.reverse(f"{get_latitude()},{get_longitude()}").raw["address"]
    except:
        _addr = None
    mo.vstack([
        mo.hstack([mo.md(f"**{_addr.get('city','')}, {_addr.get('state','')} ({_addr.get('country','')})**" if _addr else ""),
                   latitude,
                   longitude,
                  ],
                 justify='start',
                 ),
        mo.hstack([year,
                   interpolation,
                   preview,
                  ],
                  justify='start',
                 ),
    ])

    return


@app.cell
def __(
    dt,
    get_csv,
    get_df,
    get_glm,
    get_latitude,
    get_longitude,
    get_whoami,
    grid,
    gridlabd,
    io,
    line,
    marker,
    mo,
    np,
    pd,
    set_csv,
    set_df,
    set_fields,
    set_glm,
    setting_weathercsv,
    setting_weatherglm,
    setting_weatherobj,
    setting_weatheryear,
    settings,
    xaxis,
    yaxis,
):
    #
    # Preview
    #
    def preview(_):
        with mo.status.spinner("Downloading data"):
            data = io.StringIO(
                gridlabd("nsrdb_weather",
                         f"-y={year.value}",
                         f"-p={latitude.value},{longitude.value}",
                        )
            )
            df = pd.read_csv(data,parse_dates=True)
            set_df(df)
            set_csv(df.to_csv(index=False,header=False))
            set_fields(list(df.columns))
            gridlabd("nsrdb_weather",
                     f"--csv={setting_weathercsv.value}",
                     f"--glm={setting_weatherglm.value}",
                     f"--name={setting_weatherobj.value}",
                     f"--interpolate={interpolation.value}",
                     f"-y={year.value}",
                     f"-p={latitude.value},{longitude.value}",
                    )
            with open("weather.glm","r") as glm:
                set_glm(glm.read())

    def get_table():
        if get_df() is None:
            return
        return mo.vstack([
            mo.ui.table(get_df(), 
                        page_size=24,
                        selection = None,
                       ),
            mo.hstack([download_csv,download_glm],justify='start')
        ])

    def get_graph():
        if get_df() is None:
            return
        return mo.vstack([
            mo.hstack([xaxis,yaxis,mo.md("Grid:"),grid,line,marker],justify='start'),
            get_df().plot(figsize = (15,10),
                     x = xaxis.value,
                     y = yaxis.value,
                     grid = grid.value,
                     marker = marker.value,
                     linestyle = line.value,
                    ) 
                if xaxis.value and yaxis.value else mo.md("Choose fields"),
            mo.hstack([download_csv,download_glm],justify='start')
        ])

    def get_stats():
        if get_df() is None:
            return None
        data = dict(Field=[],Minimum=[],Median=[],Mean=[],Stdev=[],Maximum=[])
        for field in get_df().columns:
            X = get_df()[field]
            if type(X.min()) in [np.float64,int]:
                data["Field"].append(field)
                data["Minimum"].append(X.min().round(2))
                data["Median"].append(X.median().round(2))
                data["Mean"].append(X.mean().round(2))
                data["Stdev"].append(X.std().round(2))
                data["Maximum"].append(X.max().round(2))
        return mo.vstack([
            mo.ui.table(pd.DataFrame(data),
                        pagination = False,
                        selection = None,
                       ),
            mo.hstack([download_csv,download_glm],justify='start')
        ])

    def get_text():
        glm = get_glm()
        if glm is None:
            return
        return mo.vstack([
            mo.ui.text_area(value = glm,
                            full_width = True,
                            rows = len(glm.split("\n"))+2,
                           ),
            mo.hstack([download_csv,download_glm],justify='start')
        ])

    year = mo.ui.number(start=2000, stop=dt.datetime.now().year, label="Year:", value=setting_weatheryear.value)
    latitude = mo.ui.text(label="Latitude:", value=get_latitude())
    longitude = mo.ui.text(label="Longitude:", value=get_longitude())
    interpolation = mo.ui.dropdown(label="Interpolation (min):", options=["60","30","20","15","10","5","1"],value="60")
    preview = mo.ui.button(label="Preview", on_click=preview)
    download_glm = mo.download(label="GLM", 
                           data = get_glm(), 
                           filename = setting_weatherglm.value, 
                           disabled = (get_glm() == ""), 
                           mimetype = "text/plain")
    download_csv = mo.download(label="CSV", 
                           data = get_csv(), 
                           filename = setting_weathercsv.value, 
                           disabled = (get_csv() == ""), 
                           mimetype = "text/csv")
    nodata = mo.md(("No data" if get_whoami() else "You must register with NSRDB first (see Settings).") + "\n"*10)

    stats = get_stats()
    table = get_table()
    graph = get_graph()
    text = get_text()

    body = mo.vstack([
        mo.tabs({
            "Summary" : stats if stats else nodata,
            "Graph" : graph if graph else nodata,
            "Table" : table if table else nodata,
            "GLM" : text if text else nodata,
            "Settings" : settings,
            }),
    ])

    mo.vstack([
        body
    ])
    return (
        body,
        download_csv,
        download_glm,
        get_graph,
        get_stats,
        get_table,
        get_text,
        graph,
        interpolation,
        latitude,
        longitude,
        nodata,
        preview,
        stats,
        table,
        text,
        year,
    )


@app.cell
def __(json, mo, sys):
    default_weatherobj = "weather"
    default_weathercsv = "weather.csv"
    default_weatherglm = "weather.glm"

    default_graphxaxis = "datetime"
    default_graphyaxis = "temperature[degF]"
    default_weatheryear = 2020

    _settings_filename = sys.argv[2].replace(".py",".json")

    def load_settings(_):
        pass

    def save_settings(_):
        with open(_settings_filename,"w") as fh:
            json.dump(dict(weatherobj = default_weatherobj,
                           weathercsv = default_weathercsv,
                           weatherglm = default_weatherglm,                    
                           graphxaxis = default_graphxaxis,
                           graphyaxis = default_graphyaxis,
                           weatheryear = default_weatheryear,
                          ), 
                      fh,
                      indent = 4,
                     )

    save_settings_button = mo.ui.button(label="Save",on_click=save_settings)
    load_settings_button = mo.ui.button(label="Reset",on_click=load_settings)


    return (
        default_graphxaxis,
        default_graphyaxis,
        default_weathercsv,
        default_weatherglm,
        default_weatherobj,
        default_weatheryear,
        load_settings,
        load_settings_button,
        save_settings,
        save_settings_button,
    )


@app.cell
def __(
    load_settings_button,
    mo,
    save_settings_button,
    settings_credentials,
    settings_glmfile,
    settings_weatherdata,
):
    #
    # Settings
    #

    settings = mo.vstack([
        mo.accordion({
                "NSRDB Credentials" : settings_credentials,
                "Weather Data" : settings_weatherdata,
                "GLM File" : settings_glmfile,
            }),
        mo.hstack([
                save_settings_button,
                load_settings_button,
            ],
            justify = 'start',
             )
        ])

    return settings,


@app.cell
def __(mo):
    #
    # GLM settings
    #
    setting_weatherobj = mo.ui.text(label = "Weather object name", value = "weather")
    setting_weathercsv = mo.ui.text(label = "Weather CSV name", value = "weather.csv")
    setting_weatherglm = mo.ui.text(label = "Weather GLM name", value = "weather.glm")

    settings_glmfile = mo.vstack([
        setting_weatherobj,
        setting_weathercsv,
        setting_weatherglm,
    ])
    return (
        setting_weathercsv,
        setting_weatherglm,
        setting_weatherobj,
        settings_glmfile,
    )


@app.cell
def __(get_apikey, get_whoami, mo):
    #
    # NSRDB credentials settings
    setting_email = mo.ui.text(label = "Registration email", 
                               kind = "email", 
                               placeholder = "user.name@company.org",
                               value = get_whoami() if get_whoami() else "")
    setting_apikey = mo.ui.text(label = "Registered API key", 
                                kind = "password", 
                                placeholder = "Paste API key here",
                                value = get_apikey() if get_apikey() else "")
    setting_register = mo.ui.button(label="Register")

    settings_credentials = mo.vstack([
        mo.hstack([setting_email,setting_register],justify='start'),
        setting_apikey,
    ])


    return (
        setting_apikey,
        setting_email,
        setting_register,
        settings_credentials,
    )


@app.cell
def __(default_weatheryear, dt, mo):
    #
    # Weather graph settings
    #
    setting_graphxaxis = mo.ui.text(label = "Weather graph default x-axis", value = "datetime")
    setting_graphyaxis = mo.ui.text(label = "Weather graph default y-axis", value = "temperature[degF]")
    setting_weatheryear = mo.ui.number(start=2000, stop=dt.datetime.now().year, label="Weather year", value=default_weatheryear)

    settings_weatherdata = mo.vstack([
        setting_graphxaxis,
        setting_graphyaxis,
        setting_weatheryear,
    ])
    return (
        setting_graphxaxis,
        setting_graphyaxis,
        setting_weatheryear,
        settings_weatherdata,
    )


@app.cell
def __(me, mo):
    #
    # UI state variables
    #
    get_city, set_city = mo.state(None)
    get_location, set_location = mo.state(me)
    get_latitude, set_latitude = mo.state(f"{me.latlng[0]:.2f}")
    get_longitude, set_longitude = mo.state(f"{me.latlng[1]:.2f}")
    get_df, set_df = mo.state(None)
    get_csv, set_csv = mo.state("")
    get_glm, set_glm = mo.state("")
    get_fields, set_fields = mo.state(None)
    get_whoami, set_whoami = mo.state(None)
    get_apikey, set_apikey = mo.state(None)
    return (
        get_apikey,
        get_city,
        get_csv,
        get_df,
        get_fields,
        get_glm,
        get_latitude,
        get_location,
        get_longitude,
        get_whoami,
        set_apikey,
        set_city,
        set_csv,
        set_df,
        set_fields,
        set_glm,
        set_latitude,
        set_location,
        set_longitude,
        set_whoami,
    )


@app.cell
def __():
    #
    # Initialization
    #
    import marimo as mo
    import os, sys, io, json
    import datetime as dt
    import subprocess as sp
    import pandas as pd
    import numpy as np
    import geopy as gp
    import geocoder as gc
    from gridlabd_runner import gridlabd

    geolocator = gp.geocoders.Nominatim(user_agent="marimo")
    me = gc.ip('me')
    return (
        dt,
        gc,
        geolocator,
        gp,
        gridlabd,
        io,
        json,
        me,
        mo,
        np,
        os,
        pd,
        sp,
        sys,
    )


@app.cell
def __(gridlabd, mo):
    #
    # Gridlabd version
    #
    gridlabd_version = gridlabd("--version", binary=True, split=True)
    mo.vstack([
        mo.md("---"),
        mo.hstack([
            mo.md(f"*{gridlabd_version[0]}*"),
            mo.md("*Copyright (C) 2023, Regents of the Leland Stanford Junior University*"),
        ]),
    ])
    return gridlabd_version,


if __name__ == "__main__":
    app.run()
