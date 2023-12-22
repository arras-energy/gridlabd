import marimo

__generated_with = "0.1.58"
app = marimo.App(width="full")


@app.cell
def __(filename, load_glm, mo, new_glm, save_filename):
    #
    # Upload model
    #

    upload_file = mo.ui.file(filetypes = [".glm",".json"],
                        kind = "button",
                        label = "Upload",
                        on_change = load_glm,
                       )
    new_file = mo.ui.button(label = "New",
                       on_click = new_glm,
                      )
    mo.hstack([filename,new_file,upload_file,save_filename],justify='start')
    return new_file, upload_file


@app.cell
def __(loadclass, loadlist, loadmeter, loadmodel, loadtype, mo):
    mo.vstack([
        mo.hstack([loadclass,
                   loadlist,
                  ],
                  justify='start',
                 ),
        mo.hstack([loadtype,
                   mo.vstack([loadmeter,
                              loadmodel,
                             ]),
                  ],
                  justify='start',
                 ),
    ])
    return


@app.cell
def __(mo):
    loadclass = mo.ui.dropdown(label = "Load class",
                               options = {"3 phase load":"load","Triplex load":"triplex_load"},
                               value = "3 phase load",
                              )
    return loadclass,


@app.cell
def __(loads, mo, select_load, selected_load):
    loadlist = mo.ui.dropdown(label = "Load list",
                              options = list(loads),
                              value = selected_load,
                              on_change = select_load
                             )
    return loadlist,


@app.cell
def __(mo):
    loadtype = mo.ui.radio(label = "Load type:",
                options = ["Static","Player","Physics","Schedule","Loadshape"],
                value = "Static",
               )
    return loadtype,


@app.cell
def __(mo):
    loadmeter = mo.ui.switch(label = "metered",
                               value = False,
                              )
    return loadmeter,


@app.cell
def __(loadlist, loads, loadtype, mo, sys):
    def _static(data):
        try:
            _fields = dict([(x,mo.ui.text(value=y)) for x,y in data.items()])
            def _field(x):
                return f"<th>{x.replace('_',' ').title()}</th><td>{{{x}}}</td>"
            _rows = [_field("phases")+_field("nominal_voltage"),"<td colspan=4><hr/></td>"]
            for x in [_x for _x in ["A","B","C"] if _x in data["phases"]]:
                _rows.extend([_field(f"constant_power_{x}_real") + _field(f"constant_power_{x}_reac"),
                              _field(f"constant_current_{x}_real") + _field(f"constant_current_{x}_reac"),
                              _field(f"constant_impedance_{x}_real") + _field(f"constant_impedance_{x}_reac"),
                              "<td colspan=4><hr/></td>",
                    ])
            return mo.md(f"""<table>
                             <caption>Static load composition<hr/><caption>
                             <tr>{'</tr><tr>'.join(_rows)}</tr>
                             </table>""").batch(**_fields)
        except Exception as err:
            e_type,e_value,_ = sys.exc_info()
            return mo.md(f"""EXCEPTION: {e_type.__name__} {e_value}""")

    def _player(data):
        return mo.md(f"""<table>
    <tr><
    <table>""")

    if not loadlist.value in loads:
        loadmodel = mo.md("Select a load")
    elif loadtype.value == "Static":
        loadmodel = _static(loads[loadlist.value])
    elif loadtype.value == "Player":
        loadmodel = _player(loads[loadlist.value])
    else:
        loadmodel = mo.md(f"ERROR: load type '{loadtype.value}' not implemented yet")
    return loadmodel,


@app.cell
def __(get_glm, mo, set_glm):
    def _rename(x):
        glm = get_glm()
        glm.rename(x)
        set_glm(glm)

    filename = mo.ui.text(label = "Filename:",
                          value = get_glm().filename,
                          on_change = _rename,
                         )
    def _save(x):
        raise Exception("TODO")

    save_filename = mo.ui.button(label = "Save",
                                 on_click = _save,
                                 disabled = not get_glm().is_modified
                                )
    return filename, save_filename


@app.cell
def __(get_glm, loadclass):
    loads = get_glm().get_objects(classes=loadclass.value)
    selected_load = list(loads)[0] if len(loads) > 0 else None
    def select_load(x):
        selected_load = x
    return loads, select_load, selected_load


@app.cell
def __(GridlabdModel, mo):
    get_glm, set_glm = mo.state(GridlabdModel(name="untitled-0.json",force=True))
    def load_glm(x):
        set_glm(GridlabdModel(x[0].contents,x[0].name))
    def new_glm(x):
        set_glm(GridlabdModel())
    return get_glm, load_glm, new_glm, set_glm


@app.cell
def __():
    import marimo as mo
    import sys, os, json
    import pandas as pd
    from gridlabd_runner import gridlabd
    from gridlabd_model import GridlabdModel
    return GridlabdModel, gridlabd, json, mo, os, pd, sys


@app.cell
def __(loads):
    loads
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
