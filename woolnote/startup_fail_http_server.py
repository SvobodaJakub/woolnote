# University of Illinois/NCSA Open Source License
# Copyright (c) 2017, Jakub Svoboda.

# TODO: docstring for the file
import urllib
from http.server import BaseHTTPRequestHandler
import sys
import traceback
import ssl

from woolnote import util
from woolnote import html_constants

import argparse
from http.server import HTTPServer
import os

from woolnote import config
from woolnote.woolnote_config import WoolnoteConfig
from woolnote import util
from woolnote.task_store import Task, TaskStore
from woolnote.ui_backend import UIBackend
from woolnote.web_ui import WebUI
from woolnote.web_ui_req_handler import get_WebInterfaceHandlerLocal
from woolnote.ui_auth import WoolnoteUIAuth

def get_WebInterfaceHandlerLocal(message, list_of_messages):
    # TODO: docstring
    class WebInterfaceHandlerLocal(BaseHTTPRequestHandler):
        # TODO: docstring

        def helper_generate_page_contents(self):
            # TODO: docstring
            ss = util.sanitize_singleline_string_for_html
            sanitized_message = ss(message)
            sanitized_list_of_messages = [ss(x) for x in list_of_messages]
            sanitized_html_block_of_list_of_messages = "<br>\n".join(sanitized_list_of_messages)
            page_content = "<html><body>{}<br>\n{}</body></html>".format(
                sanitized_message,
                sanitized_html_block_of_list_of_messages
            )
            return page_content

        def req_handler(self):
            # TODO: docstring
            page_content = self.helper_generate_page_contents()
            try:
                self.wfile.write(page_content.encode("utf-8"))
            except ssl.SSLEOFError:
                # TODO in woolnote.py - why is suppress_ragged_eofs ignored?
                util.dbgprint("ssl.SSLEOFError (#TODO in the code)")
            return

        def do_GET(self):
            # TODO: docstring
            self.do_HEAD()
            self.req_handler()
            return

        def do_POST(self):
            # TODO: docstring
            self.do_HEAD()
            self.req_handler()

        def do_HEAD(self):
            # TODO: docstring
            '''
            Handle a HEAD request.
            '''
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

    return WebInterfaceHandlerLocal


def serve_error_message_forever():

    WebInterfaceHandlerLocal = get_WebInterfaceHandlerLocal("Read README.txt to set up woolnote.", config.DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES)  # TODO


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


    def serve_on_port(port, use_ssl=False):
        server = get_server_on_port(port, use_ssl)
        util.dbgprint("trying serve_forever")
        server.serve_forever()

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

    serve_forever(server_http, server_https)
