import marimo

__generated_with = "0.1.66"
app = marimo.App()


@app.cell
def __(mo):
    mo.md(f"""
    # GridLAB-D Converters
    """)
    return


@app.cell
def __(mo, os):
    _options = set([os.path.splitext(x)[0].split("2")[0] for x in os.listdir(os.environ["GLD_ETC"]) if "2" in x and not "-" in x and x.endswith(".py")])
    file = mo.ui.file(label = "Upload file",
                      filetypes = [f".{x}" for x in _options],
                      multiple = True,
                     )
    file
    return file,


@app.cell
def __(file, mo):
    mo.vstack([
        mo.md("Preview"),
        mo.tabs(dict([(x.name,
                       mo.ui.text_area(value=x.contents,
                                       rows=10,
                                       full_width = True
                                      )) for x in file.value])),
    ]) if len(file.value) > 0 else mo.md("")

    return


@app.cell
def __(file, mo):
    if len(file.value) > 0:
        primary = mo.ui.dropdown(label = "Primary file",
                                 options = [x.name for x in file.value],
                                 value = file.name(0),
                                )
    else:
        primary = mo.md("Upload your file(s)")
    primary
    return primary,


@app.cell
def __(file, mo, primary):
    if len(file.value) > 0:
        secondary = mo.ui.multiselect(label = "Secondary files",
                                      options = [x.name for x in file.value if x.name != primary.value],
                                      value = [],
                                )
    else:
        secondary = mo.md("")
    secondary
    return secondary,


@app.cell
def __(os, primary):
    try:
        from_format = os.path.splitext(primary.value)[1][1:]
    except:
        from_format = None

    return from_format,


@app.cell
def __(converter_dict, from_format, mo):
    try:
        _options = [x for x in converter_dict[from_format] if x]
    except:
        _options = []
    from_type = mo.ui.dropdown(label = "From type",
                               options = _options,
                              )
    from_type if len(_options) > 0 else mo.md("")
    return from_type,


@app.cell
def __(converter_dict, from_format, from_type, mo):
    try:
        _options = [x for x in converter_dict[from_format][from_type.value] if x]
    except:
        _options = []
    to_format = mo.ui.dropdown(label = "To format",
                                 options = _options,
                                )
    to_format if len(_options) > 0 else mo.md("")
    return to_format,


@app.cell
def __(converter_dict, from_format, from_type, mo, to_format):
    try:
        _options = [x for x in converter_dict[from_format][from_type.value][to_format.value] if x]
    except:
        _options = []
    to_type = mo.ui.dropdown(label = "To type", options = _options)
    to_type if len(_options) > 0 else mo.md("")
    return to_type,


@app.cell
def __(os):
    converter_list = [os.path.splitext(x)[0] for x in os.listdir(os.environ["GLD_ETC"]) if "2" in x and x.endswith(".py")]
    converter_dict = {}
    for _converter in converter_list:
        _from,_to = [x.split("-") for x in _converter.split("2")]
        if len(_from) == 1:
            _from.append(None)
        elif len(_from) > 2:
            _from = [_from[0],"-".join(_from[1:])]
        if not _from[0] in converter_dict:
            converter_dict[_from[0]] = {}
        converter_dict[_from[0]] = {_from[1]:{}}
        if len(_to) == 1:
            _to.append(None)
        elif len(_to) > 2:
            _to = [_to[0],"-".join(_to[1:])]
        if not _to[0] in converter_dict[_from[0]][_from[1]]:
            converter_dict[_from[0]][_from[1]] = {_to[0]:{}}
        converter_dict[_from[0]][_from[1]][_to[0]] = {_to[1]:os.path.join(
            os.environ["GLD_ETC"],_converter,".py")}
    return converter_dict, converter_list


@app.cell
def __(from_format, from_type, mo, os, primary, to_format, to_type):
    if to_format.value:
        _from = f" -f {from_format}-{from_type.value}" if from_type.value else ""
        _to = f" -t {to_format.value}-{to_type.value}" if to_type.value else ""
        convert_files = mo.ui.text_area(label = "Converter command",
                        value = f"""gridlabd convert -i "{primary.value}"{_from} -o "{os.path.splitext(primary.value)[0]+"."+to_format.value}"{_to}""",
                        full_width = True,
                        rows = 5
                       )
    else:
        convert_files = mo.md("Choose the 'to' format")
    convert_files
    return convert_files,


@app.cell
def __(mo, os, output_file):

    def delete_output(_):
        os.remove(output_file)
    if os.path.exists(output_file):
        download_file = mo.download(data = None,
                                label = "Download "+output_file,
                                filename = output_file,
                               )
        delete_file = mo.ui.button(label = "X",
                               on_click = delete_output,
                              )
    else:
        download_file = mo.md("")
        delete_file = mo.md("")

    return delete_file, delete_output, download_file


@app.cell
def __(mo, os, primary):
    output_file = os.path.splitext(primary.value)[0]+".zip"
    def run_converter(_):
        with open(output_file,"w") as fh:
            pass
    convert = mo.ui.button(label = "Run converter",
                           on_click = run_converter,
                          )
    return convert, output_file, run_converter


@app.cell
def __(convert, delete_file, download_file, mo):
    mo.hstack([convert,download_file,delete_file],justify='start')
    return


@app.cell
def __(mo):
    mo.md("---")
    return


@app.cell
def __(gld):
    gld.Gridlabd("--version=all",binary=True).run()
    return


@app.cell
def __(mo):
    mo.md(f"Marimo version {mo.__version__}")
    return


@app.cell
def __():
    import os, sys
    import marimo as mo
    import gridlabd_runner as gld
    return gld, mo, os, sys


if __name__ == "__main__":
    app.run()
