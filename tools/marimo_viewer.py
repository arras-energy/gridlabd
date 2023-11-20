import marimo

__generated_with = "0.1.47"
app = marimo.App(width="full")


@app.cell
def __(load_glm, mo, set_file):
    #
    # File upload
    #
    filename = mo.ui.file(
        filetypes=[".json"],
        kind="button",
        label="GridLAB-D model file (JSON)",
        on_change=lambda x: set_file(load_glm(x)),
    )
    filename
    return filename,


@app.cell
def __(filename, mo):
    #
    # Filename witness
    #
    mo.md(f"**Current file**: `{filename.name(0)}`")
    return


@app.cell
def __(change_labels, change_satellite, get_file, mo):
    #
    # Display options
    #
    _data = get_file()
    if _data is None:
        selector = mo.md("Invalid model")
    elif len(_data) == 0:
        selector = mo.md("No GridLAB-D objects to view")
    else:
        keys = list(_data["classes"])
        class_select = mo.ui.dropdown(
            options=keys,
            allow_select_none=False,
            value=keys[0],
        )
        with_header = mo.ui.switch(value=False)
        map_type = mo.ui.switch(value=False, on_change=change_satellite)
        with_labels = mo.ui.switch(value=False, on_change=change_labels)
        selector = mo.hstack(
            [
                mo.md("Select object class to display: "),
                class_select,
                mo.md("Show header data"),
                with_header,
                mo.md("Show object labels"),
                with_labels,
                mo.md("Satellite view:"),
                map_type,
            ],
            justify="start",
        )
    selector
    return class_select, keys, map_type, selector, with_header, with_labels


@app.cell
def __(data_view, get_mapview, mo, simulation_view, table_view):
    #
    # Show the chosen view
    #
    main_view = mo.tabs({
        "Objects": table_view,
        "Properties": data_view,
        "Map": get_mapview(),
        "Simulation" : simulation_view,
    })
    main_view
    return main_view,


@app.cell
def __(get_status, mo):
    #
    # Status information
    #
    mo.md(f"""
    ---

    {get_status()}
    """)
    return


@app.cell
def __(class_select, get_file, mo, select_object, set_status, with_header):

    #
    # Objects view
    #

    table_view = None

    def update_table():
        global table_view
        _data = get_file()
        if not _data is None and "classes" in _data and len(_data["classes"]) > 0 and class_select.selected_key:
            _classes = _data["classes"]
            table_data = _classes[class_select.value].copy()
            if with_header.value == False:
                table_data.drop(["id","rank","clock","rng_state","guid","flags","parent"],inplace=True,axis=1,errors='ignore')
            table_view = mo.ui.table(table_data,
                                     pagination = True,
                                     selection = 'single',
                                     on_change = select_object,
                                     )
            set_status(f"Class '{class_select.value}' has {len(table_data)} objects.")
        else:
            table_view = mo.md("None")

    update_table()
    return table_view, update_table


@app.cell
def __(class_select, get_title, glm, mo, set_property):
    #
    # Properties view
    #
    get_object, set_object = mo.state(None)

    data_view = None

    def select_object(x):
        global data_view
        set_object(x)
        if not x is None:
            rows = mo.vstack([mo.ui.text(label=get_title(prop),
                                         disabled = (prop in glm["header"]),
                                         value=str(row.iloc[0]),
                                         on_change = lambda value:set_property(x.index[0],prop,value),
                                        ) for prop,row in get_object().transpose().iterrows()])
            data_view = f"""
    <table bgcolor="white">
    <caption>{get_title(class_select.value)} <b>{x.index[0]}</b><hr/></caption>
    <tr><td>{rows}</td><tr>
    </table>
    """
        else:
            data_view = mo.md("None")
    return data_view, get_object, select_object, set_object


@app.cell
def __(get_file, mo, px):
    #
    # Map view
    #
    def load_map():
        if get_file() is None or "data" not in get_file() or len(get_file()["data"]) == 0:
            return None
        nodes = get_file()["nodes"]
        if nodes is None or len(nodes) == 0:
            return None
        lines = get_file()["lines"]
        data = get_file()["data"]

        # nodes
        # map = px.scatter_mapbox(
        #     lat = nodes['latitude'],
        #     lon = nodes['longitude'],
        #     hover_name = nodes['name'],
        #     text = nodes['name'] if get_labels() else None,
        #     zoom = 15,
        #     # TODO: add hover_data flags, e.g., dict(field:bool,...)
        # )
        map = px.scatter_mapbox(nodes,
                                lat = 'latitude',
                                lon = 'longitude',
                                hover_name = 'name',
                                text = 'name' if get_labels() else None,
                                zoom = 15,
                                hover_data = dict(
                                    latitude=False,
                                    longitude=False,
                                    nominal_voltage=True,
                                    phases=True,
                                ),
                               )

        # lines
        latlon = nodes.reset_index()[['name','latitude','longitude']].set_index('name')
        latlon = dict([(n,(xy['latitude'],xy['longitude'])) for n,xy in latlon.iterrows()])
        valid = [(n,x,y) for n,x,y in zip(lines['name'],lines['from'],lines['to']) if x in latlon and y in latlon]
        names = [None] * 3 * len(valid)
        names[0::3] = [x[0] for x in valid]
        names[1::3] = [x[0] for x in valid]
        lats = [None] * 3 * len(valid)
        lats[0::3] = [latlon[x[1]][0] for x in valid]
        lats[1::3] = [latlon[x[2]][0] for x in valid]
        lons = [None] * 3 * len(valid)
        lons[0::3] = [latlon[x[1]][1] for x in valid]
        lons[1::3] = [latlon[x[2]][1] for x in valid]
        map.add_trace(dict(hoverinfo = 'skip',
                           lat = lats,
                           lon = lons,
                           line = dict(color='#636efa'),
                           mode = 'lines',
                           subplot = 'mapbox',
                           type = 'scattermapbox',
                           showlegend = False))

        if get_satellite():
            map.update_layout(
                mapbox_style="white-bg",
                mapbox_layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": "United States Geological Survey",
                        "source": [                 "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                        ],
                    },
                  ])
        else:    
            map.update_layout(mapbox_style="open-street-map")
        map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        set_mapview(map)

    get_labels, set_labels = mo.state(False)
    get_satellite, set_satellite = mo.state(False)
    get_mapview, set_mapview = mo.state(None)

    def change_labels(x):
        set_labels(x)
        load_map()

    def change_satellite(x):
        set_satellite(x)
        load_map()

    load_map()
    return (
        change_labels,
        change_satellite,
        get_labels,
        get_mapview,
        get_satellite,
        load_map,
        set_labels,
        set_mapview,
        set_satellite,
    )


@app.cell
def __(err, json, mo, pd, set_status):
    #
    # Data load
    #
    glm = None

    def load_glm(upload):
        if upload is None:
            set_status("Select a file to view")
            return pd.DataFrame({})
        try:
            global glm
            glm = json.loads(upload[0].contents.decode())
            result = refresh_model()
            set_status(f"File '{upload[0].name}' contains {len(result['data'])} objects.")
            return result
        except Exception as err:
            set_status(f"Exception: {err}!")

    def set_property(obj,prop,value):
        glm["objects"][obj][prop] = value
        set_file(refresh_model())

    def refresh_model():
        assert glm["application"] == "gridlabd"
        assert glm["version"] >= "4.3.3"
        data = pd.DataFrame(glm["objects"]).transpose()
        data.index.name = "name"
        data.reset_index(inplace=True)
        if "latitude" in data and "longitude" in data:
            data['latitude'] = [float(x) for x in data['latitude']]
            data['longitude'] = [float(x) for x in data['longitude']]
            nodes = data.loc[~data["latitude"].isnull()&~data["longitude"].isnull()]
            lines = data.loc[~data["from"].isnull()&~data["to"].isnull()]
        else:
            nodes = None
            lines = None
        data.set_index(["class","name"],inplace=True)
        classes = {}
        for oclass in data.index.get_level_values(0).unique():
            classes[oclass] = data.loc[oclass].dropna(axis=1,how='all')
        return dict(
            data = data,
            classes = classes,
            nodes = nodes,
            lines = lines)

    get_file, set_file = mo.state(load_glm(None))
    return get_file, glm, load_glm, refresh_model, set_file, set_property


@app.cell
def __(glm, json, mo, subprocess):
    simulation_view = None

    def run_simulation(x=None):
        output = "Click <b>Run</b> to start simulation"
        global simulation_view
        if type(glm) is dict and "objects" in glm:
            with open("model.json","w") as fh:
                json.dump(glm,fh,indent=4)
                result = subprocess.run(["gridlabd","model.json"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                output = f"""GridLAB-D run {'succeeded' if result.returncode == 0 else 'failed'} (exit code {result.returncode})
    ```
    {result.stdout.decode()}
    ```
    """
        simulation_view = mo.vstack([run_button,mo.md(output)])

    run_button = mo.ui.button(label = "Run",on_click=run_simulation)
    run_simulation()
    return run_button, run_simulation, simulation_view


@app.cell
def __():
    #
    # Utilities
    #
    def get_title(x):
        import re
        return re.sub('[^A-Za-z0-9]',' ',x).title()
    return get_title,


@app.cell
def __(mo):
    #
    # Status variables
    #
    get_status, set_status = mo.state("")
    return get_status, set_status


@app.cell
def __():
    #
    # Requirements
    #
    import os, sys, json
    import asyncio
    import marimo as mo
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    return asyncio, go, json, mo, np, os, pd, px, sys


if __name__ == "__main__":
    app.run()
