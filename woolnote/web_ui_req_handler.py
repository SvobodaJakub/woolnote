# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

# TODO: docstring for the file
import urllib
from http.server import BaseHTTPRequestHandler
import sys
import traceback
import ssl

from woolnote import util
from woolnote import html_constants
from woolnote import tests


# web interface request handler
###############################


def get_WebInterfaceHandlerLocal(woolnote_config, task_store, web_ui, ui_auth):
    """
    Returns the class for the web request handler which has access to data in the arguments. (Because the class is
    then used in such a way that it's not possible to pass additional arguments to its __init__().)
    Args:
        woolnote_config (woolnote.woolnote_config.WoolnoteConfig): The used shared instance of the current woolnote configuration (e.g. virtual folders).
        task_store (woolnote.task_store.TaskStore): The primary task store currently used.
        web_ui (woolnote.web_ui.WebUI): Web UI handlers that are called by req_handler_*() methods in the returned class.
        ui_auth (woolnote.ui_auth.WoolnoteUIAuth): The authentication module to be used for checking authentication credentials and authorizing access.

    Returns:
        type: class WebInterfaceHandlerLocal(BaseHTTPRequestHandler) that holds the arguments in its scope
    """
    class WebInterfaceHandlerLocal(BaseHTTPRequestHandler):

        HTTP_STATIC_RESOURCES = {
            "/uikit-2.27.1.gradient-customized.css": {
                "page_content": html_constants.CSS_UIKIT_2_27_1_STYLE_OFFLINE,
                "Content-Type": "text/css",
                "Cache-Control": "max-age=259200, public",
            },
            "/favicon.ico": {
                "page_content": "",
                "Content-Type": "text/html",
                "Cache-Control": "max-age=3600, public",
            },
        }

        def __init__(self, *args, **kwargs):
            """
            Request handler that calls web_ui.py to do the heavy lifting.

            Args:
                *args ():
                **kwargs ():
            """
            self.last_request_get_dict = {}
            self.last_request_post_data_dict = {}
            self.last_request_path = ""
            self.last_request_headers = {}
            self.authenticated = False
            if tests.TEST_FRAMEWORK_ENABLED:
                tests.gen_serializable_test_new_request()
                tests.gen_serializable_test_instance("WebInterfaceHandlerLocal", self)
            super().__init__(*args, **kwargs)

        @tests.gen_serializable_test_method()
        def _test_repr(self):
            """
            Prints some properties. For testing purposes.

            Returns:
                str
            """
            repr = ""
            repr += "self.last_request_get_dict = {}\n".format(self.last_request_get_dict)
            repr += "self.last_request_post_data_dict = {}\n".format(self.last_request_post_data_dict)
            repr += "self.last_request_path = {}\n".format(self.last_request_path)
            repr += "self.last_request_headers = {}\n".format(self.last_request_headers)
            repr += "self.authenticated = {}\n".format(self.authenticated)
            return repr

        @tests.gen_serializable_test_method()
        def helper_check_permanent_pwd(self):
            """
            Checks whether the password provided in the GET data (in the request path) is correct.

            Returns:
                bool: True if the password should be accepted, False otherwise.
            """
            try:
                full_path = self.last_request_path
                user_supplied_key, user_supplied_value = full_path.split("=")
                if not util.safe_string_compare(user_supplied_key.strip(), "/woolnote?woolauth"):
                    return False
                if 100 > len(user_supplied_value.strip()) > 6:
                    return ui_auth.check_permanent_pwd(user_supplied_value.strip())
                return False
            except:
                return False

        @tests.gen_serializable_test_method()
        def helper_check_one_time_pwd(self):
            """
            Checks whether the one-time password provided in the GET data (in the request path) is correct.

            Returns:
                bool: True if the OTP should be accepted, False otherwise.
            """
            try:
                full_path = self.last_request_path
                user_supplied_key, user_supplied_value = full_path.split("=")
                if not util.safe_string_compare(user_supplied_key.strip(), "/woolnote?otp"):
                    return False
                if 100 > len(user_supplied_value.strip()) > 6:
                    return ui_auth.check_one_time_pwd(user_supplied_value.strip())
                return False
            except:
                return False

        @tests.gen_serializable_test_method()
        def helper_get_request_authentication(self):
            """
            Sets self.authenticated to True or False based on whether the request is authenticated from path or from
            cookies.

            Returns:
                None:
            """

            self.authenticated = False

            # hashing&salting so that string comparison doesn't easily allow timing attacks
            if self.helper_check_permanent_pwd():
                self.authenticated = True
                # will display page_content = web_ui.page_list_notes()
            if self.helper_check_one_time_pwd():
                self.authenticated = True
                # will display page_content = web_ui.page_list_notes()
            try:
                cookies = self.last_request_headers['Cookie'].split(";")
                for cookie in cookies:
                    keyval = cookie.split("=")
                    key = keyval[0].strip()
                    if key == "auth":
                        val = keyval[1].strip()
                        # hashing&salting so that string comparison doesn't easily allow timing attacks
                        # if val == ui_auth.return_cookie_authenticated():
                        if util.safe_string_compare(val, ui_auth.return_cookie_authenticated()):
                            self.authenticated = True
            except Exception as exc:
                util.dbgprint("exception in cookie handling {}".format(str(exc)))
            return self.authenticated

        def get_request_path(self):
            """
            Copies the request path into self.last_request_path.

            Returns:
                None:
            """

            try:
                self.input_data_last_request_path(self.path)
            except:
                self.input_data_last_request_path("")


        def get_request_data(self):
            """
            Copies the request GET and POST data into self.last_request_get_dict, self.last_request_path,
            self.last_request_post_data_dict and sets self.authenticated (bool) based based on the data and cookie.

            Returns:
                None:
            """

            try:
                self.input_data_last_request_get_dict(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            except:
                self.input_data_last_request_get_dict({})
            try:
                self.input_data_last_request_path(self.path)
            except:
                self.input_data_last_request_path("")
            try:
                last_request_post_data = self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8")
            except:
                last_request_post_data = ""
            try:
                self.input_data_last_request_post_data_dict(urllib.parse.parse_qs(last_request_post_data))
            except:
                self.input_data_last_request_post_data_dict({})
            try:
                # convert http.client.HTTPMessage to dict
                last_request_headers = {k: v for k, v in self.headers.items()}
                self.input_data_last_request_headers(last_request_headers)
            except:
                self.input_data_last_request_headers({})

            self.authenticated = False
            self.helper_get_request_authentication()

        @tests.gen_serializable_test_method()
        def req_handler_authenticated(self):
            """
            Request handler for authenticated requests. To be used by helper_generate_page_contents().

            Returns:
                str: Contents of the resulting page.
            """
            page_content = "<html><body>N/A</body></html>"
            # reload the config settings (the config note could have been changed by the user)
            woolnote_config.read_from_config_note(task_store)

            def history_go_back():
                """
                Set the page to go back in history - rewriting self.last_request_get_dict

                Returns:
                    None:
                """
                nonlocal page_content
                try:
                    util.dbgprint("history_back - try")
                    # history_back_id might not exist -> except
                    # history_back_id id might not exist in the history dict -> except
                    try:
                        history_id = self.last_request_get_dict["history_back_id"][0]
                    except:
                        util.dbgprint("history_back_id not found, using main_list")
                        history_id = "main_list"
                    if history_id == "main_list":
                        pass
                    else:
                        self.last_request_get_dict = web_ui.get_last_get_request_from_history_id(history_id)
                        web_ui.set_last_request(self.last_request_post_data_dict, self.last_request_get_dict)
                    util.dbgprint("history_back - end of try")
                except:
                    util.dbgprint("history_back - except")
                    pass

            def display_content_after_history_back_during_request_processing():
                """
                Display the right page after history_go_back() during processing of a request by setting page_content
                using the correct type of page listing notes. If the page to be displayed is not clear, it just
                displays a list of all notes which is not saved back to history because the action is not what we'd
                want to go back to in the first place.

                Returns:
                    None:
                """
                nonlocal page_content
                if "action" not in self.last_request_get_dict:
                    page_content = web_ui.page_list_notes(no_history=True)
                elif self.last_request_get_dict["action"][0] == "page_list_folder":
                    page_content = web_ui.page_list_folder()
                elif self.last_request_get_dict["action"][0] == "page_list_tag":
                    page_content = web_ui.page_list_tag()
                elif self.last_request_get_dict["action"][0] == "page_search_notes":
                    page_content = web_ui.page_search_notes()
                else:
                    page_content = web_ui.page_list_notes(no_history=True)

            # handle request to display a list from history (back/cancel buttons, not browser history)
            if "action" in self.last_request_get_dict:
                if self.last_request_get_dict["action"][0] == "history_back":
                    history_go_back()

            # copy the data about the current request into the web_ui so that it can act on them as well
            web_ui.set_last_request(self.last_request_post_data_dict, self.last_request_get_dict)

            try:
                if "action" not in self.last_request_get_dict:
                    page_content = web_ui.page_list_notes()

                elif self.last_request_get_dict["action"][0] == "page_display_note":
                    page_content = web_ui.page_display_note()
                elif self.last_request_get_dict["action"][0] == "req_dismiss_reminder_and_display_note":
                    web_ui.req_note_dismiss_reminder()
                    page_content = web_ui.page_display_note()

                elif self.last_request_get_dict["action"][0] == "req_display_otp":
                    web_ui.req_display_otp()
                    history_go_back()
                    display_content_after_history_back_during_request_processing()

                elif self.last_request_get_dict["action"][0] == "page_list_folder":
                    page_content = web_ui.page_list_folder()

                elif self.last_request_get_dict["action"][0] == "page_list_tag":
                    page_content = web_ui.page_list_tag()

                elif self.last_request_get_dict["action"][0] == "page_search_notes":
                    page_content = web_ui.page_search_notes()

                elif self.last_request_get_dict["action"][0] == "page_list_trash":
                    page_content = web_ui.page_list_trash()

                elif self.last_request_get_dict["action"][0] == "page_edit_note":
                    page_content = web_ui.page_edit_note()

                elif self.last_request_get_dict["action"][0] == "page_add_new_note":
                    page_content = web_ui.page_add_new_note()

                elif self.last_request_get_dict["action"][0] == "page_delete_taskid":
                    page_content = web_ui.page_delete_notes()

                elif self.last_request_get_dict["action"][0] == "req_note_checkboxes_save":
                    web_ui.req_note_checkboxes_save()
                    page_content = web_ui.page_display_note()

                elif self.last_request_get_dict["action"][0] == "req_save_edited_note":
                    web_ui.req_save_edited_note()
                    page_content = web_ui.page_edit_note()

                elif self.last_request_get_dict["action"][0] == "req_save_new_note":
                    web_ui.req_save_new_note()
                    page_content = web_ui.page_edit_note()

                elif self.last_request_get_dict["action"][0] == "req_save_new_single_task_line":
                    web_ui.req_save_new_single_task_line()
                    page_content = web_ui.page_display_note()

                elif self.last_request_get_dict["action"][0] == "page_import_prompt":
                    page_content = web_ui.page_import_prompt()

                elif self.last_request_get_dict["action"][0] == "page_export_prompt":
                    page_content = web_ui.page_export_prompt()

                elif self.last_request_get_dict["action"][0] == "req_import_notes":
                    web_ui.req_import_notes()
                    history_go_back()
                    display_content_after_history_back_during_request_processing()

                elif self.last_request_get_dict["action"][0] == "req_export_notes":
                    web_ui.req_export_notes()
                    history_go_back()
                    display_content_after_history_back_during_request_processing()

                elif self.last_request_get_dict["action"][0] == "req_delete_taskid":
                    web_ui.req_delete_taskid()
                    history_go_back()
                    display_content_after_history_back_during_request_processing()

                elif self.last_request_get_dict["action"][0] == "req_note_list_manipulate_foldermove":
                    web_ui.req_note_list_manipulate_foldermove()
                    history_go_back()
                    display_content_after_history_back_during_request_processing()

                elif self.last_request_get_dict["action"][0] == "req_note_list_manipulate_tagadd":
                    web_ui.req_note_list_manipulate_tagadd()
                    history_go_back()
                    display_content_after_history_back_during_request_processing()

                elif self.last_request_get_dict["action"][0] == "req_note_list_manipulate_tagdel":
                    web_ui.req_note_list_manipulate_tagdel()
                    history_go_back()
                    display_content_after_history_back_during_request_processing()

                elif self.last_request_get_dict["action"][0] == "page_note_list_multiple_select":
                    page_content = web_ui.page_note_list_multiple_select()

                else:
                    page_content = web_ui.page_list_notes()

            except Exception as exc:
                etype, evalue, etraceback = sys.exc_info()
                ss = util.sanitize_singleline_string_for_html
                cmps = util.convert_multiline_plain_string_into_safe_html
                page_content = """<html><body>Exception {exc}:<br/>
                    <pre>{tra}</pre><br/>
                    <a href="woolnote">list notes</a></body></html>""".format(exc=ss(repr(exc)), tra=cmps(
                    repr(traceback.format_exception(etype, evalue, etraceback))))
                page_content = page_content.replace("\\n", "<br>\n")
            return page_content

        @tests.gen_serializable_test_method()
        def req_handler_unauthenticated(self):
            """
            Request handler for unauthenticated requests.

            Returns:
                str: Contents of the resulting page.
            """
            page_content = "<html><body>N/A</body></html>"
            try:
                if self.last_request_get_dict["action"][0] == "page_display_note":
                    task_id = self.last_request_get_dict["taskid"][0]
                    task_pubauthid = self.last_request_get_dict["pubauthid"][0]
                    page_content = web_ui.unauth_page_display_note_public(task_id, task_pubauthid)
            except:
                pass
            return page_content

        @tests.gen_serializable_test_method()
        def helper_generate_page_contents(self):
            """
            Generates contents for the main woolnote functionality - the pages, request handlers, etc. Both
            authenticated and unauthenticated. Based on the current request POST, GET, path, cookies.

            Returns:
                str: The generated page.
            """
            page_content = "<html><body>N/A</body></html>"
            if self.authenticated:
                page_content = self.req_handler_authenticated()
            else:
                # NOT authenticated!
                page_content = self.req_handler_unauthenticated()
            return page_content

        @tests.gen_serializable_test_method()
        def req_handler(self):
            """
            Handles requests to both static and dynamic content.
            Returns contents that are intended to be written to self.wfile.

            Returns:
                str:
            """
            resource_found = False
            # handle static requests
            for resource in self.HTTP_STATIC_RESOURCES:
                if self.last_request_path.startswith(resource):
                    page_content = self.HTTP_STATIC_RESOURCES[resource]["page_content"]
                    resource_found = True
                    break
            # handle dynamic requests
            if not resource_found:
                page_content = self.helper_generate_page_contents()
            return page_content

        @tests.gen_serializable_test_method()
        def input_data_last_request_path(self, val):
            """
            This function exists so that input data can be captured by the test generator so that this class is testable.
            """
            self.last_request_path = val

        @tests.gen_serializable_test_method()
        def input_data_last_request_get_dict(self, val):
            """
            This function exists so that input data can be captured by the test generator so that this class is testable.
            """
            self.last_request_get_dict = val

        @tests.gen_serializable_test_method()
        def input_data_last_request_post_data_dict(self, val):
            """
            This function exists so that input data can be captured by the test generator so that this class is testable.
            """
            self.last_request_post_data_dict = val

        @tests.gen_serializable_test_method()
        def input_data_last_request_headers(self, val):
            """
            This function exists so that input data can be captured by the test generator so that this class is testable.
            """
            self.last_request_headers = val

        # not decorated on purpose
        def output_data_wfile_write(self, val):
            """
            This function exists so that output data can be captured by the test generator so that this class is testable.
            """
            try:
                self.wfile.write(val.encode("utf-8"))
            except ssl.SSLEOFError:
                # TODO in woolnote.py - why is suppress_ragged_eofs ignored?
                util.dbgprint("ssl.SSLEOFError (#TODO in the code)")

        def do_GET(self):
            self.get_request_data()
            self.do_HEAD()
            self.output_data_wfile_write(self.req_handler())
            return

        def do_POST(self):
            self.get_request_data()

            # instead of do_HEAD(), do similar work
            # the same response
            self.send_response(200)
            # reply for POST can only be text/html because of how woolnote works
            self.send_header("Content-Type", "text/html")
            self.send_header("X-Frame-Options", "DENY")
            # set auth cookie
            if self.authenticated:
                self.send_header("Set-cookie", "auth=" + ui_auth.return_cookie_authenticated() + "; SameSite=Strict; HttpOnly")
            self.end_headers()
            # end of what is otherwise done in do_HEAD()

            self.output_data_wfile_write(self.req_handler())

        def do_HEAD(self):
            self.get_request_path()
            self.send_response(200)
            resource_found = False
            for resource in self.HTTP_STATIC_RESOURCES:
                if self.last_request_path.startswith(resource):
                    try:
                        content_type = self.HTTP_STATIC_RESOURCES[resource]["Content-Type"]
                        self.send_header("Content-Type", content_type)
                    except:
                        pass
                    try:
                        cache_control = self.HTTP_STATIC_RESOURCES[resource]["Cache-Control"]
                        self.send_header("Cache-Control", cache_control)
                    except:
                        pass
                    resource_found = True
                    break
            if not resource_found:
                self.send_header("Content-Type", "text/html")
            self.send_header("X-Frame-Options", "DENY")
            if self.authenticated:
                self.send_header("Set-cookie", "auth=" + ui_auth.return_cookie_authenticated() + "; SameSite=Strict; HttpOnly")
            self.end_headers()
            if tests.TEST_FRAMEWORK_ENABLED:
                # let the test generator record it, so that the internal state is captured in the tests
                self._test_repr()

    return WebInterfaceHandlerLocal
