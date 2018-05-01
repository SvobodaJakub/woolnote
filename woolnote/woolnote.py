# qpy:webapp:Woolnote
# qpy:fullscreen
# qpy://127.0.0.1:8088/woolnote?woolauth=please_change_me

# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.


# TODO: docstring for the file
"""TODO docstring"""

import argparse
from http.server import HTTPServer
import os
import ssl

from woolnote import config
from woolnote.woolnote_config import WoolnoteConfig
from woolnote import util
from woolnote.task_store import Task, TaskStore, TaskStoreTestingNoWrite
from woolnote.ui_backend import UIBackend
from woolnote.web_ui import WebUI
from woolnote.web_ui_req_handler import get_WebInterfaceHandlerLocal
from woolnote.ui_auth import WoolnoteUIAuth
from woolnote import tests


# info about time comparison using string comparison:
# >>> a
# '2016-02-25 22:04:29'
# >>> b
# '2016-02-25 22:06:14'
# >>> a<b
# True
# >>> a>b
# False
# >>> sorted(x)
# ['2016-02-25 22:04:29', '2016-02-25 22:06:14', '2016-02-26', '2016-02-26 06:07:01']


#  + TODO:
#  + - input must be sanitized
#  +   - task name must not contain newlines, or else an escalation to other fields in the note may be possible
#  + TODO: task body newlines vs <br>
#  + TODO: sanitize all user input
#  - TODO: sanitize all file input
#  + TODO: html escaping
#  + TODO: folders
#  + TODO: tags
#  + TODO: common html constructs into functions
#  + TODO: common html styles into functions
#  - TODO: very light background colors that signify the action - green=view, blue=edit/new, red=delete, white=settings
#  + TODO: main page offers folders and tags on top, in two columns to save vertical space, notes are below
#  + TODO: main page checkboxes for actions
#      #+ TODO: delete
#      #+ TODO: add tag
#      #+ TODO: remove tag
#      #- TODO: replace tag list
#      #+ TODO: move to folder
#      #x TODO: touch (move to top)
#  + TODO: main page note order by lamport clock
#  + TODO: edit note JS widgets that add common formatting - [x], ** **, *** ***, **** ****, __ __, --- ---, * bullet, - bullet, indented bullets
#      #+ TODO: make the formatting work -> make a parser
#      #+ TODO: formatting works only if both tags are on the same line -> sth like a line "2**16=...." would not get misinterpreted
#  + TODO: web interface - move the save button up so that it is visible while editing the task body on mobile devices
#  + TODO: detect if /sdcard/tmp/ exists and prepend it to the paths if yes (have a list of possible path, use the one that exists or use nothing if nothing exists)
#  - TODO: ignore tags with the string "" (empty)
#  + TODO: export everything to dropbox
#  + TODO: import everything from dropbox; do not overwrite local notes that are newer
#  + TODO: fulltext search
#  + TODO: webkit do not zoom on textarea edit - scroll down for device width - http://stackoverflow.com/questions/7073396/disable-zoom-on-input-focus-in-android-webpage
#  - TODO: task body delimiter should be randomly generated on every save instead of using taskid; check that import works with that
#  - TODO: create tests for everything
#  + TODO: js hide div containing everything else during note edit - https://stackoverflow.com/questions/4528085/toggle-show-hide-div-with-button
#  + TODO: split the UI to backend & frontend; frontend is purely HTML, backend deals with data manipulation
#  + TODO: search not case sensitive
#  - TODO: interactive import
#  + TODO: import error if lamport clock is lower
#  + TODO: LAST-IMPORT-LAMPORT-CLOCK; import error if lower than EXPORT-LAMPORT-CLOCK
#  +x TODO: public notes have a unique random pubid (different from taskid); taskid is not exposed in any way; pubid is saved in task's metadata (new field); loading tasks loads also a dict of all pubids; pubids accessible via a special get request without login (make sure to NOT grant auth cookie)
#  - TODO: edit mode for pubid - changes saved to a special staging area with a colorful diff
#  + TODO: markup vs. plain format
#  - TODO:
#  - TODO:
#  - TODO:
#  - TODO:
#  - TODO:
#  - TODO:





# if __name__ == "__main__":

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("command", nargs="?", default="", help="CLI command")
args = parser.parse_args()

# TODO: the arguments do not have sense anymore; delete or come up with sth useful
# TODO: have useful help, sourced from the main docstring

if args.command == "adfasfd":
    pass
if args.command == "list":
    pass


if config.DISPLAY_STARTUP_HELP:
    from woolnote import startup_fail_http_server
    startup_fail_http_server.serve_error_message_forever()


task_store = TaskStore(os.path.join(config.PATH_SAVE_DB, config.FILE_TASKS_DAT))
task_store_trash = TaskStore(os.path.join(config.PATH_SAVE_DB, config.FILE_TASKS_TRASH_DAT))

if tests.TEST_FRAMEWORK_ENABLED:
    # if replaying tests, unplickle all the other supporting instances before web_ui is instantiated
    if tests.PICKLETEST_REPLAY:
        tests.integration_pre_rerun("web_ui")

        # NOTE: this is how data structures can be restored if necessary
        # task_store = tests.integration_unpickle_data("web_ui", "task_store")
        # task_store_trash = tests.integration_unpickle_data("web_ui", "task_store_trash")
        # woolnote_config = tests.integration_referenced_data("web_ui")["woolnote_config"]
        # ui_auth = tests.integration_referenced_data("web_ui")["ui_auth"]

        task_store = TaskStoreTestingNoWrite(os.path.join(config.PATH_SAVE_DB, config.FILE_TASKS_DAT))
        task_store_trash = TaskStoreTestingNoWrite(os.path.join(config.PATH_SAVE_DB, config.FILE_TASKS_TRASH_DAT))

task_store.task_store_load()
task_store_trash.task_store_load()
util.tasks_backup(task_store, task_store_trash)

ui_auth = WoolnoteUIAuth()
woolnote_config = WoolnoteConfig()
ui_backend = UIBackend(task_store, task_store_trash)
web_ui = WebUI(task_store, task_store_trash, ui_backend, woolnote_config, ui_auth)

if tests.TEST_FRAMEWORK_ENABLED:

    tests.integration_instance("web_ui", "web_ui", web_ui)
    tests.integration_instance("web_ui", "woolnote_config", woolnote_config)
    tests.integration_instance("web_ui", "ui_auth", ui_auth)

    if tests.PICKLETEST_REPLAY:
        # the order of these tests matter if they are run with shared state
        # note that it might be necessary to COMPLETELY replicate the whole environment for the test to result in an identical run
        # that's why it is necessary to run `TEST_reset_tasks_dat.sh` before both recording and replaying
        tests.integration_rerun("web_ui")
        tests.integration_rerun("html_page_templates")
        tests.integration_rerun("util")
        quit()
    else:
        tests.gen_serializable_test_beginning()

        # NOTE: this is how data structures can be restored if necessary

        # recording state at the current moment (first state)
        # tests.integration_pickle_data("web_ui", "task_store", task_store)
        # tests.integration_pickle_data("web_ui", "task_store_trash", task_store_trash)
        # tests.integration_pickle_data("web_ui", "ui_backend", ui_backend)
        # tests.integration_pickle_data("web_ui", "woolnote_config", woolnote_config)
        # tests.integration_pickle_data("web_ui", "ui_auth", ui_auth)

        # this will record their state at the latest moment (last state)
        # tests.integration_referenced_data("web_ui")["task_store"] = task_store
        # tests.integration_referenced_data("web_ui")["task_store_trash"] = task_store_trash
        # tests.integration_referenced_data("web_ui")["ui_backend"] = ui_backend
        # tests.integration_referenced_data("web_ui")["woolnote_config"] = woolnote_config
        # tests.integration_referenced_data("web_ui")["ui_auth"] = ui_auth

# below is web interface that is not necessary for tests of web_ui.py and the things that are called from that module

WebInterfaceHandlerLocal = get_WebInterfaceHandlerLocal(woolnote_config, task_store, web_ui, ui_auth)

def get_server_on_port(port, use_ssl=False):
    server = HTTPServer(("", port), WebInterfaceHandlerLocal)
    if use_ssl:
        try:
            util.dbgprint("use_ssl=True, trying")
            ssl_cert_path = os.path.join(config.PATH_DIR_FOR_SSL_CERT_PEM, config.FILE_CERT_PEM)
            ssl_key_path = os.path.join(config.PATH_DIR_FOR_SSL_KEY_PEM, config.FILE_KEY_PEM)
            server.socket = ssl.wrap_socket(server.socket, certfile=ssl_cert_path,
                                            keyfile=ssl_key_path, server_side=True,
                                            suppress_ragged_eofs=True)
            # TODO: for some reason, suppress_ragged_eofs is ignored
        except:
            util.dbgprint("use_ssl=True, FAILED!")
    else:
        util.dbgprint("use_ssl=False")
    util.dbgprint("returning server")
    return server


# def serve_on_port(port, use_ssl=False):
#     server = get_server_on_port(port, use_ssl)
#     util.dbgprint("trying serve_forever")
#     server.serve_forever()


# Using threads this way doesn't work correctly on Python 3.3 and maybe the code is wrong
# (either one of them doesn't work or when they work both, then changes in one are not reflected in the other one)
# try:
#     from threading import Thread
#     Thread(target=serve_on_port, args=[8088, False]).start()
# except Exception as exc:
#     etype, evalue, etraceback = sys.exc_info()
#     ss = sanitize_singleline_string_for_html
#     cmps = convert_multiline_plain_string_into_safe_html
#     dbgprint("""Cannot start SSL server.\n
#         Exception {exc}:\n
#         {tra}\n
#         """.format(exc=ss(repr(exc)), tra=cmps(repr(traceback.format_exception(etype, evalue, etraceback)))))
# serve_on_port(8088, False)

server_http = get_server_on_port(config.HTTP_PORT, False)
server_https = get_server_on_port(config.HTTPS_PORT, True)


def serve_forever(*servers):
    # https://stackoverflow.com/questions/60680/how-do-i-write-a-python-http-server-to-listen-on-multiple-ports
    import select
    while True:
        r, w, e = select.select(servers, [], [], 10)
        for server in servers:
            if server in r:
                server.handle_request()


# from android import Android
# droid = Android()
# droid.webViewShow('http://127.0.0.1:8088/woolnote?woolauth=sleepysheep')

serve_forever(server_http, server_https)
