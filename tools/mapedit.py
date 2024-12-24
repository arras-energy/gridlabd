import marimo

__generated_with = "0.10.6"
app = marimo.App(width="full")


@app.cell
def _(mo, mu):
    # State variables
    get_modelname, set_modelname = mo.state("")
    get_version, set_version = mo.state(mu.version)
    return get_modelname, get_version, set_modelname, set_version


@app.cell
def _(get_version, mo):
    # Open button
    open_ui = mo.ui.file(
        filetypes=([".glm"] if get_version() else []) + [".json"], label="Open"
    )
    return (open_ui,)


@app.cell
def _(get_modelname, mo):
    # Download button
    download_ui = mo.ui.button(label="Download", disabled=get_modelname() == "")
    return (download_ui,)


@app.cell
def _(mo, mu, open_ui):
    mo.sidebar(mu.render_sidebar(open_ui))
    return


@app.cell
def _(download_ui, get_modelname, mo, open_ui, set_modelname):
    # Screen layout
    name_ui = mo.ui.text(
        label="as",
        value=get_modelname(),
        on_change=set_modelname,
        placeholder="Open a model",
    )
    mo.hstack([open_ui, download_ui, name_ui], justify="start")
    return (name_ui,)


@app.cell
def _(mo, mu, open_ui, set_modelname):
    # Model convert/load
    set_modelname("")
    mo.stop(len(open_ui.value) == 0, "HINT: open a GridLAB-D GLM or JSON model")
    model, _result = mu.model(source=open_ui, folder="/tmp")
    set_modelname(open_ui.name(0))
    mo.md("\n".join(_result)) if _result else None
    return (model,)


@app.cell
def _(mo):
    get_view,set_view = mo.state({"zoom":2.75,"center":{"lat":39,"lon":-100}})
    return get_view, set_view


@app.cell
def _(get_view, mo):
    _step = {(x+1):16*2.0**(-x) for x in range(15)} # steps at zoom levels

    def reset(event):
        get_view()["zoom"] = 15

    def zoomin(event):
        get_view()["zoom"]+=1

    def zoomout(event):
        get_view()["zoom"]-=1

    def north(event):
        zoom = get_view()["zoom"]
        get_view()["center"]["lat"] += _step[int(zoom)]

    def south(event):
        zoom = get_view()["zoom"]
        get_view()["center"]["lat"] -= _step[int(zoom)]

    def east(event):
        zoom = get_view()["zoom"]
        get_view()["center"]["lon"] += _step[int(zoom)]

    def west(event):
        zoom = get_view()["zoom"]
        get_view()["center"]["lon"] -= _step[int(zoom)]

    reset_button = mo.ui.button(label="o",on_click=reset)
    zoomin_button = mo.ui.button(label="+", on_click=zoomin)
    zoomout_button = mo.ui.button(label="-", on_click=zoomout)
    north_button = mo.ui.button(label="&uparrow;",on_click=north)
    south_button = mo.ui.button(label="&downarrow;",on_click=south)
    east_button = mo.ui.button(label="&rightarrow;",on_click=east)
    west_button = mo.ui.button(label="&leftarrow;",on_click=west)
    set_button = mo.ui.button(label="=")
    del_button = mo.ui.button(label="x")
    return (
        del_button,
        east,
        east_button,
        north,
        north_button,
        reset,
        reset_button,
        set_button,
        south,
        south_button,
        west,
        west_button,
        zoomin,
        zoomin_button,
        zoomout,
        zoomout_button,
    )


@app.cell
def _(
    del_button,
    east_button,
    get_view,
    mo,
    model,
    mu,
    north_button,
    reset_button,
    set_button,
    south_button,
    west_button,
    zoomin_button,
    zoomout_button,
):
    def _lat():
        degrees,minutes = divmod(get_view()['center']['lat'],60)
        return mo.md(f"{abs(degrees*60)} {minutes}")

    def _lon():
        return mo.md(f"{get_view()['center']['lon']}")

    def render_mapedit():
        return mo.vstack(
            [
                mo.hstack([set_button,north_button,del_button],justify='center'),
    mo.hstack([west_button,reset_button,east_button],justify='center'),
    mo.hstack([zoomin_button,south_button,zoomout_button],justify='center'),
                mo.hstack([_lat(),_lon()],justify='center'),
                mu.render_map(model,**get_view()),
            ]
        )
    return (render_mapedit,)


@app.cell
def _(mo, model, mu):
    # Sidebar routes
    mo.stop(
        model.application != "gridlabd",
        "model is not a GridLAB-D application data file",
    )
    mo.routes(
        {
            "#/globals": lambda: mu.render_globals(model),
            "#/modules": lambda: mu.render_modules(model),
            "#/classes": lambda: mu.render_classes(model),
            "#/objects": lambda: mu.render_objects(model),
            "#/map": lambda: mu.render_map(model),
            mo.routes.CATCH_ALL: lambda: mu.render_status(model),
        }
    )
    return


@app.cell
def _(subprocess):
    def gridlabd(*args, bin=True, **kwargs):
        if not "capture_output" in kwargs:
            kwargs["capture_output"] = True
        try:
            return subprocess.run(
                ["gridlabd.bin" if bin else "gridlabd"] + list(args), **kwargs
            )
        except:
            return None
    return (gridlabd,)


@app.cell
def _():
    # Imports and setup
    import marimo as mo
    import json
    import os
    import sys
    import subprocess
    from collections import namedtuple
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio
    import moutils as mu
    return go, json, mo, mu, namedtuple, os, pd, pio, px, subprocess, sys


@app.cell
def _():
    # {x:y for x,y in model.objects.items() if "bustype" in y and y["bustype"] == "SWING"}
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
