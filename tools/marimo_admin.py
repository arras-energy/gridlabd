import marimo

__generated_with = "0.1.59"
app = marimo.App()


@app.cell
def __(mo):
    mo.md("# GridLAB-D Marimo Dashboard")
    return


@app.cell
def __(actions, editor, mo, refresh):
    refresh
    mo.tabs({
        "Marimo Tools" : actions,
        # "Settings" : mo.vstack([
        #     mo.hstack([mo.md("Use editor"),editor],justify = 'start'),
        #     mo.hstack([mo.md("Refresh rate"),refresh],justify = 'start'),
        # ])
        "Settings" : mo.md("""
        <table>
        <tr><th>Use editor</th><td>{editor}</td></tr>
        <tr><th>Refresh rate></th><td>{refresh}</td></tr>
        </table>
        """).batch(editor=editor,refresh=refresh)
    })

    return


@app.cell
def __(gridlabd):
    available = gridlabd("marimo","index",split=True)
    return available,


@app.cell
def __(mo):
    refresh = mo.ui.refresh(options = ["1s","2s","5s","10s","20s","30s","1min"],
                            default_interval = "1s",
                           )
    return refresh,


@app.cell
def __(mo):
    editor = mo.ui.switch()
    return editor,


@app.cell
def __(available, editor, get_active, gridlabd, inactive, mo, psutil):
    def _action(x):
        if x in get_active():
            proc = psutil.Process(get_active()[x]["pid"])
            proc.terminate()
        elif editor.value:
            gridlabd("marimo","open","--edit",x)
        else:
            gridlabd("marimo","open",x)

    def _url(x):
        port = get_active()[x]["port"]
        return f"""<b><a href="http://localhost:{port}/" target="_blank">{x.replace("_"," ").title()}</a></b> """

    _active = get_active()
    _args = dict([(x,mo.ui.button(label="Stop" if x in _active else "Start",on_click=lambda _,x=x:_action(x))) for x in available])
    actions = mo.md("<table><tr><th>Action</th><th>Tool name</th><th>Port</th><th>Process</th></tr>"+"\n".join([f"""<tr><td>{{{x}}}</td><td>{x.replace("_"," ").title() if x in inactive else _url(x)}</td><td>{_active[x]["port"] if x in _active else ""}</td><td>{_active[x]["pid"] if x in _active else ""}</td></tr>""" for x in available])+"</table>").batch(**_args)
    return actions,


@app.cell
def __(available, mo, os, psutil, re, refresh, requests):
    refresh

    def _getfile(body):
        """Get the filename from the marimo reply"""
        for item in body.strip().split("\n"):
            if item.startswith("<marimo-filename hidden>"):
                return re.sub(r"<[^>]*>","",item)

    def _getpid(file):
        """Get the pid from the filename"""
        for pid in psutil.pids():
            try:
                proc = psutil.Process(pid)
                cmd = proc.cmdline()
                if len(cmd) < 4:
                    continue
                if cmd[3] == file:
                    return pid
            except psutil.AccessDenied:
                pass
            except psutil.NoSuchProcess:
                pass
        return None

    _list = [] # list of marimo apps running
    for _port in range(2718,2800):
        try:
            _r = requests.get(f"http://localhost:{_port}/")
            if _r.status_code == 200:
                _file = _getfile(_r.text)
                _list.append([_port,
                              _getpid(_file),
                              os.path.basename(_file) \
                              .replace("marimo_","") \
                              .replace(".py",""),
                             ])
        except requests.exceptions.ConnectionError as _:
            pass

    _active = dict([(y[2],dict(pid=None if y[1] == '-' else y[1],port=y[0])) for y in _list if y[2] in available])

    get_active, set_active = mo.state(_active)
    return get_active, set_active


@app.cell
def __(available, get_active):
    inactive = [x for x in available if x not in get_active()]
    return inactive,


@app.cell
def __():
    import marimo as mo
    import sys, os
    import requests
    import re
    import psutil
    from gridlabd_runner import gridlabd
    return gridlabd, mo, os, psutil, re, requests, sys


if __name__ == "__main__":
    app.run()
