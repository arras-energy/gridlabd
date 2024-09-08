import marimo

__generated_with = "0.7.0"
app = marimo.App(width="full", app_title="GridLAB-D REST API Test")


@app.cell
def __(mo):
    #
    # URL
    #
    get_url, set_url = mo.state("")
    url_ui = mo.ui.text(
        label="GridLAB-D REST server URL:",
        value=get_url(),
        placeholder="http://127.0.0.1:5000/<TOKEN>",
        on_change=set_url,
        full_width=True,
    )
    url_ui
    return get_url, set_url, url_ui


@app.cell
def __(mo):
    #
    # Session
    #
    get_session, set_session = mo.state(1)
    session_ui = mo.ui.number(
        label="Session ID: ",
        start=1,
        stop=10,
        value=get_session(),
        on_change=set_session,
    )
    session_ui
    return get_session, session_ui, set_session


@app.cell
def __(
    close_send_ui,
    download_send_ui,
    files_send_ui,
    get_close_result,
    get_download_result,
    get_files_result,
    get_open_result,
    get_run_result,
    get_upload_result,
    mo,
    open_send_ui,
    run_send_ui,
    upload_send_ui,
):
    #
    # Tabs
    #
    tab_ui = mo.ui.tabs(
        {
            "open": mo.vstack([open_send_ui, get_open_result()], justify="start"),
            "close": mo.vstack(
                [close_send_ui, get_close_result()], justify="start"
            ),
            "files": mo.vstack(
                [files_send_ui, get_files_result()], justify="start"
            ),
            "run": mo.vstack([run_send_ui, get_run_result()], justify="start"),
            "download": mo.vstack(
                [download_send_ui, get_download_result()], justify="start"
            ),
            "upload": mo.vstack(
                [upload_send_ui, get_upload_result()], justify="start"
            ),
        }
    )
    tab_ui
    return tab_ui,


@app.cell
def __(mo, send, table):
    #
    # Open
    #
    get_open_result, set_open_result = mo.state(
        table({}, caption="(click to send to get a response)")
    )
    open_send_ui = mo.ui.button(
        label="Send", on_click=lambda x: send("open", set_open_result)
    )
    return get_open_result, open_send_ui, set_open_result


@app.cell
def __(mo, send, table):
    #
    # Close
    #
    get_close_result, set_close_result = mo.state(
        table({}, caption="(click to send to get a response)")
    )
    close_send_ui = mo.ui.button(
        label="Send", on_click=lambda x: send("close", set_close_result)
    )
    return close_send_ui, get_close_result, set_close_result


@app.cell
def __(mo, os, send, table):
    #
    # Files
    #
    get_files_result, set_files_result = mo.state(
        table({}, caption="(click to send to get a response)")
    )
    get_files_path, set_files_path = mo.state("")
    files_send_button = mo.ui.button(
        label="Send",
        on_click=lambda x: send(
            os.path.join("files", get_files_path()), set_files_result
        ),
    )
    files_send_path = mo.ui.text(
        label="Path", value=get_files_path(), on_change=set_files_path
    )
    files_send_ui = mo.hstack(
        [files_send_button, files_send_path], justify="start"
    )
    return (
        files_send_button,
        files_send_path,
        files_send_ui,
        get_files_path,
        get_files_result,
        set_files_path,
        set_files_result,
    )


@app.cell
def __(mo, os, send, table):
    #
    # Run
    #
    get_run_result, set_run_result = mo.state(
        table({}, caption="(click to send to get a response)")
    )
    get_run_path, set_run_path = mo.state("")
    run_send_button = mo.ui.button(
        label="Send",
        on_click=lambda x: send(
            os.path.join("run", get_run_path()), set_run_result
        ),
    )
    run_send_path = mo.ui.text(
        label="Options", value=get_run_path(), on_change=set_run_path
    )
    run_send_ui = mo.hstack([run_send_button, run_send_path], justify="start")
    return (
        get_run_path,
        get_run_result,
        run_send_button,
        run_send_path,
        run_send_ui,
        set_run_path,
        set_run_result,
    )


@app.cell
def __(mo, os, send, table):
    #
    # Download
    #
    get_download_result, set_download_result = mo.state(
        table({}, caption="(click to send to get a response)")
    )
    get_download_path, set_download_path = mo.state("")
    download_send_button = mo.ui.button(
        label="Send",
        on_click=lambda x: send(
            os.path.join("download", get_download_path()), set_download_result
        ),
    )
    download_send_path = mo.ui.text(
        label="Filename", value=get_download_path(), on_change=set_download_path
    )
    download_send_ui = mo.hstack(
        [download_send_button, download_send_path], justify="start"
    )
    return (
        download_send_button,
        download_send_path,
        download_send_ui,
        get_download_path,
        get_download_result,
        set_download_path,
        set_download_result,
    )


@app.cell
def __(mo, os, send, table):
    #
    # Upload
    #
    get_upload_result, set_upload_result = mo.state(
        table({}, caption="(click to send to get a response)")
    )
    get_upload_files, set_upload_files = mo.state({})
    upload_send_button = mo.ui.button(
        label="Send",
        on_click=lambda x: send(
            os.path.join("upload"),
            set_upload_result,
            method="POST",
            getdata=get_upload_files,
        ),
    )
    upload_file_browser = mo.ui.file_browser(on_change=set_upload_files)
    upload_send_ui = mo.hstack(
        [upload_send_button, upload_file_browser], justify="start"
    )
    return (
        get_upload_files,
        get_upload_result,
        set_upload_files,
        set_upload_result,
        upload_file_browser,
        upload_send_button,
        upload_send_ui,
    )


@app.cell
def __(get_session, get_url, json, mo, os, rq):
    def table(data, caption=None):
        """Convert response to table"""
        result = "<table>"
        if caption:
            result += f"<caption>{caption.replace(' ','&nbsp;')}</caption>"
        for n, row in enumerate(data):
            result += "<tr>"
            for m, item in enumerate(row):
                result += f"<td><div align=left><code>{item}</code></div></td>" if m > 0 else f"<th valign=top>{item.title()}</th>"
            result += "</tr>"
        result += "</table>"
        return mo.md(result)


    def send(command, callback, method="GET", getdata=None):
        """Send command and set response"""
        if method == "GET":
            req = rq.get(url=os.path.join(get_url(), str(get_session()), command))
        elif method == "POST":
            files = dict([(x.name,open(x.path,"rb")) for x in getdata()])
            req = rq.post(
                url=os.path.join(get_url(), str(get_session()), command),
                files=files,
            )
        else:
            raise Exception(f"unsupported method {method}")
        if req.status_code == 200:
            result = json.loads(req.content.decode("utf-8"))
            result["content"] = json.dumps(result["content"],indent=4).replace("\n","<br/>").replace(" ","&nbsp;")
        elif req.status_code == 400:
            try:
                result = json.loads(req.content.decode("utf-8"))
            except:
                result = {"message":"(none)","status":"ERROR"}
        else:
            result = {"HTTP error": req.status_code}
        callback(table(result.items(), caption="Response<hr/>"))
    return send, table


@app.cell
def __():
    import os
    import marimo as mo
    import requests as rq
    import json
    import pandas as pd
    return json, mo, os, pd, rq


if __name__ == "__main__":
    app.run()
