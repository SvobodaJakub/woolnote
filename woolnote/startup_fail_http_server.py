# University of Illinois/NCSA Open Source License
# Copyright (c) 2017, Jakub Svoboda.

# TODO: docstring for the file
from woolnote import systemencoding
from http.server import BaseHTTPRequestHandler
import ssl

from http.server import HTTPServer
import os

from woolnote import config
from woolnote import util
from woolnote.web_ui_req_handler import get_WebInterfaceHandlerLocal


def get_WebInterfaceHandlerLocal(message, list_of_messages):
    """
    Returns the class for the web request handler which has access to data in the arguments. (Because the class is
    then used in such a way that it's not possible to pass additional arguments to its __init__().)
    Args:
        message (str): Error message to display.
        list_of_messages (list[str]): Additional error messages to display.

    Returns:
        type: class WebInterfaceHandlerLocal(BaseHTTPRequestHandler) that holds the arguments in its scope
    """
    class WebInterfaceHandlerLocal(BaseHTTPRequestHandler):
        """
        Simple handler that displays a static page with the defined list of error messages (taken from captured scope).
        """

        def helper_generate_page_contents(self):
            """
            Generates contents for the static error page. Doesn't process any additional user data.

            Returns:
                str: The generated page.
            """
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
            """
            Handles requests to content. There is only one page, so it is very simple.

            Returns:
                None:
            """
            page_content = self.helper_generate_page_contents()
            try:
                self.wfile.write(page_content.encode("utf-8"))
            except ssl.SSLEOFError:
                # TODO in woolnote.py - why is suppress_ragged_eofs ignored?
                util.dbgprint("ssl.SSLEOFError (#TODO in the code)")
            return

        def do_GET(self):
            self.do_HEAD()
            self.req_handler()
            return

        def do_POST(self):
            self.do_HEAD()
            self.req_handler()

        def do_HEAD(self):
            '''
            Handle a HEAD request.
            '''
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

    return WebInterfaceHandlerLocal


def serve_error_message_forever():
    """
    Starts a stripped down version of http request handler that serves a single page with a list of errors from
    config.py and blocks forever.

    Returns: None
    """

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
