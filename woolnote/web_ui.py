# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

# TODO: docstring for the file
# TODO: think about moving functionality to backend

import hashlib

from woolnote import util
from woolnote import config
from woolnote import html_page_templates
from woolnote.task_store import Task
from woolnote import tests


# Web UI frontend
#################

class WebUI():
    def __init__(self, task_store, task_store_trash, ui_backend, woolnote_config, ui_auth):
        """
        Web UI that uses the specified ui_backend (which performs most data manipulation), the specified task stores
        for storing the data, the specified ui_auth for performing authentication actions, and the specified
        woolnote_config holding configuration for the whole program.
        The web ui is to be used by a server that correctly sets the properties self.last_request_post_data_dict,
        self.last_request_get_dict using the method set_last_request() before calling a method of the web ui. The server
        can also use the method get_last_get_request_from_history_id() to retrieve an older set of get request data to
        inject them back into set_last_request() and effectively go back in history (the server has to pay attention
        from which pages to which pages it is valid to go to and this is currently not documented).

        Args:
            task_store (woolnote.task_store.TaskStore):
            task_store_trash (woolnote.task_store.TaskStore):
            ui_backend (woolnote.ui_backend.UIBackend):
            woolnote_config (woolnote.woolnote_config.WoolnoteConfig):
            ui_auth (woolnote.ui_auth.WoolnoteUIAuth):
        """
        super().__init__()

        # history_back gets the proper history hash (history_id) so that it uses that instead
        self.last_request_post_data_dict = {}
        self.last_request_get_dict = {}
        self.error_msg_queue_list = []  # error messages to be displayed on a task list
        self.error_msg_queue_note = []  # error messages to be displayed on a note

        # history of visited paths so that a "back" link can be provided
        self.last_history_dict_of_links = {}

        # this is used for permanent actions like delete so that get requests with permanent effects cannot be cached and mistakenly used in other sessions
        self.sess_action_auth = util.create_id_task()  # create a new random auth string

        # this is used for permanent actions like import/export so that get requests with permanent effects cannot be cached and mistakenly used in other sessions or by going back in the browser's history
        self.nonce_action_auth = util.create_id_task()  # create a new random auth string
        self.nonce_action_auth_valid_uses = 0  # do not allow the value to be used at beginning

        self.task_store = task_store
        self.task_store_trash = task_store_trash
        self.ui_backend = ui_backend
        self.woolnote_config = woolnote_config
        self.ui_auth = ui_auth

    @tests.integration_method("web_ui")
    def set_last_request(self, postdict, getdict):
        """
        To be used by the http request handler before calling any methods for a new request.

        The web ui is to be used by a server that correctly sets the properties self.last_request_post_data_dict,
        self.last_request_get_dict using the method set_last_request() before calling a method of the web ui.

        Args:
            postdict (Union[Dict, Dict[str, List[str]]]):
            getdict (Dict[str, List[str]]):

        Returns:
            None:
        """
        self.last_request_post_data_dict = postdict
        self.last_request_get_dict = getdict

    @tests.integration_method("web_ui")
    def get_last_get_request_from_history_id(self, id):
        """
        To be used by the http request handler to go back in request history. Returns a dict of GET request keys and
        values associated with the provided history ID. History ID is a hash of the request keys and values of interest.

        Args:
            id (str): History id where to go to.

        Returns:
            Dict: GET request keys and values associated with the history ID.

        """
        # - to be used by the http request handler to go back in request history
        return self.last_history_dict_of_links[id].copy()

    @tests.integration_method("web_ui")
    def save_history(self, req_keys_to_save, alt_task_store_name=None):
        """
        To be used by the other methods in this class - the methods that display a listing of notes, so that notes can go back to the same listing.

        Args:
            req_keys_to_save (Union[List[str], List]):
            alt_task_store_name (Union[None, str]):

        Returns:
            str: history_id
        """
        history_id = "main_list"  # fallback string
        _hd = self.last_request_get_dict
        _hk = req_keys_to_save
        _lhgd = {k: _hd[k] for k in _hd if k in _hk}
        if _lhgd:
            if alt_task_store_name is not None:
                _lhgd.update({"alt_task_store_name": [alt_task_store_name]})
            # save only if the dict is nonempty, so that favicon.ico does not overwrite it
            history_id = hashlib.sha256(repr(_lhgd).encode("utf-8")).hexdigest()
            self.last_history_dict_of_links[history_id] = _lhgd
        return history_id

    @tests.integration_method("web_ui")
    def helper_convert_msg_queue_list_to_list_for_output(self):
        """
        Creates a new static list of warnings collected so far, empties the list.

        Returns:
            List[str]: List of warnings.
        """
        result = []
        if self.error_msg_queue_list:
            # this order of reference shuffling ensures that a race condition doesn't result in lost messages in the oddball case these variables are also edited in a different true thread
            msg_list = self.error_msg_queue_list
            self.error_msg_queue_list = []
            result = [str(x) for x in msg_list]
        return result

    @tests.integration_method("web_ui")
    def helper_convert_msg_queue_note_to_list_for_output(self):
        """
        Creates a new static list of warnings collected so far, empties the list.

        Returns:
            List[str]: List of warnings.
        """
        result = []
        if self.error_msg_queue_note:
            # this order of reference shuffling ensures that a race condition doesn't result in lost messages in the oddball case these variables are also edited in a different true thread
            msg_list = self.error_msg_queue_note
            self.error_msg_queue_note = []
            result = [str(x) for x in msg_list]
        return result


    @tests.integration_method("web_ui")
    def helper_sessactionauth_is_wrong(self):
        """
        Gets the GET value sessactionauth and finds out whether it is wrong

        Returns:
            bool: True if sessactionauth is wrong
        """
        wrong = not util.safe_string_compare(self.sess_action_auth, self.last_request_get_dict["sessactionauth"][0])
        if wrong:
            util.dbgprint("sessactionauth is wrong - {}".format(self.last_request_get_dict["sessactionauth"][0]))
        return wrong

    @tests.integration_method("web_ui")
    def helper_action_get_request_is_wrong(self, action_name):
        """
        Gets the GET value "action" and finds out whether it is wrong
        Throws an exception if the data don't exist so that the exception bubbles up.

        Args:
            action_name (string): The action string that is expected to be right

        Returns:
            bool: True if the provided action name and the contents of the action dictionary key differ
        """
        wrong = not util.safe_string_compare(action_name, self.last_request_get_dict["action"][0])
        return wrong

    @tests.integration_method("web_ui")
    def helper_action_post_request_is_wrong(self, action_name, dict_key=None):
        """
        Gets the POST value "action" and finds out whether it is wrong
        Doesn't throw an exception if the data don't exist becacuse it is sometimes expected that they don't and so
        it just returns True.

        Args:
            action_name (string): The action string that is expected to be right
            dict_key (string): Alternative dictionary string to use (instead of "action")

        Returns:
            bool: True if the provided action name and the contents of the action dictionary key differ or if the dict key doesn't exist.
        """
        try:
            if dict_key is None:
                dict_key = "action"
            wrong = not util.safe_string_compare(action_name, self.last_request_post_data_dict[dict_key][0])
            return wrong
        except:
            return True


    @tests.integration_method("web_ui")
    def helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none(self, key_name):
        """
        Returns either the first GET value of the specified key or (if it doesnt exist) None.

        Args:
            key_name (str): Key of the GET value.

        Returns:
            Union[str, None]: Either the first GET value of the specified key or (if it doesnt exist) None.
        """
        try:
            return self.last_request_get_dict[key_name][0]
        except:
            return None


    @tests.integration_method("web_ui")
    def helper_retrieve_last_request_post_dict_key_val_index_zero_or_return_none(self, key_name):
        """
        Returns either the first POST value of the specified key or (if it doesnt exist) None.

        Args:
            key_name (str): Key of the POST value.

        Returns:
            Union[str, None]: Either the first POST value of the specified key or (if it doesnt exist) None.
        """
        try:
            return self.last_request_post_data_dict[key_name][0]
        except:
            return None


    @tests.integration_method("web_ui")
    def create_new_nonce(self):
        """
        Creates a new nonce and sets how many tries are left (just one try). To be used for pages whose actions must not be repeated by reloading the page / resending the request.

        Returns:
            str: Nonce.
        """

        self.nonce_action_auth = util.create_id_task()  # create a new random auth string
        self.nonce_action_auth_valid_uses = 1
        return self.nonce_action_auth

    @tests.integration_method("web_ui")
    def check_one_time_nonce(self, user_supplied_nonce):
        """
        Checks whether the supplied nonce is correct, only if tries are left.
        Nonce is disabled after 1st successful use.
        To be used for pages whose actions must not be repeated by reloading the page / resending the request.
        The method's name is redundant, but clear (nonce == number used once).

        Args:
            user_supplied_nonce (str): The potentially wrong or malicious nonce the user provided. Decreases the number of tries left.

        Returns:
            bool: Whether the user-supplied nonce is correct and allowed.
        """

        if self.nonce_action_auth_valid_uses > 0:
            self.nonce_action_auth_valid_uses -= 1
            ret = util.safe_string_compare(user_supplied_nonce, self.nonce_action_auth)
            if ret is True:  # explicitly checking for boolean True
                return True
            return False
        return False

    @tests.integration_method("web_ui")
    def helper_get_alt_task_store_name(self):
        """
        Returns alt_task_store_name if present in the get data or None if not present.

        Returns:
            None: alt_task_store_name if present in the get data or None if not present.
        """
        return self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("alt_task_store_name")

    @tests.integration_method("web_ui")
    def req_display_otp(self):
        """
        Puts a new generated one-time password to the self.error_msg_queue_list so that it is displayed.

        Returns:
            None:
        """

        ret = self.ui_auth.create_new_one_time_pwd()
        if ret is not None:
            self.error_msg_queue_list.append(ret)

    @tests.integration_method("web_ui")
    def helper_save_task_itself_from_req(self, task):
        """
        Reads data for a new/saved note from POST data, performs sanitization, and correctly saves the data to a note
        (that also entails resetting the reminder flag if due date changes, correctly processing body text based on
        formatting used, setting the correct values for the formatting property)

        Args:
            task (woolnote.task_store.Task): Task into which POST data are saved.

        Returns:
            None:
        """
        tainted_task_name = self.last_request_post_data_dict.get("taskname", [config.DEFAULT_TASKNAME])[0]
        tainted_task_folder = self.last_request_post_data_dict.get("taskfolder", [config.DEFAULT_FOLDER])[0]
        tainted_task_pubauthid = self.last_request_post_data_dict.get("taskpubauthid", [util.create_id_task()])[0]
        tainted_task_tags = self.last_request_post_data_dict.get("tasktags", [""])[0]
        tainted_task_body = self.last_request_post_data_dict.get("taskbody", [""])[0]
        tainted_due_date = self.last_request_post_data_dict.get("duedate", [""])[0]
        tainted_formatting = self.last_request_post_data_dict.get("formatting", ["markup"])[0]

        self.ui_backend.helper_sanitize_task_before_save(task_to_be_updated=task,
                                                         tainted_task_name=tainted_task_name,
                                                         tainted_task_folder=tainted_task_folder,
                                                         tainted_task_pubauthid=tainted_task_pubauthid,
                                                         tainted_task_tags=tainted_task_tags,
                                                         tainted_task_body=tainted_task_body,
                                                         tainted_due_date=tainted_due_date,
                                                         tainted_formatting=tainted_formatting)


    @tests.integration_method("web_ui")
    def req_save_new_single_task_line(self):
        """
        Saves a new single task line from the GET and POST data above the specified single task line id.
        (This functionality is useful for entering single lines into frequently used places in notes.)

        Args:

        Returns:
            None:
        """
        if self.helper_action_get_request_is_wrong("req_save_new_single_task_line"):
            self.error_msg_queue_note.append("Single note line has not been saved.")
            return

        if self.helper_action_post_request_is_wrong("req_save_new_single_task_line", "post_action"):
            # this POST value is not present when the page is visited from history
            # missing POST data and not doing this check would delete all checkboxes on the page
            self.error_msg_queue_note.append("Single note line has not been saved - wrong request (page reload?).")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_note.append("Single note line has not been saved - wrong session.")
            return

        single_note_line_id = util.sanitize_singleline_string_for_tasksave(self.last_request_post_data_dict["single_note_line_id"][0])
        self.error_msg_queue_note.append("Saving one line under ID " + str(single_note_line_id))
        single_note_line_text = ""
        try:
            single_note_line_text = util.sanitize_singleline_string_for_tasksave(self.last_request_post_data_dict["single_note_line_text"][0])
            self.error_msg_queue_note.append("Saving one line: '{}'".format(str(single_note_line_text)))
        except:
            self.error_msg_queue_note.append("Not saving an empty line.")

        single_note_line_prepend_minus_space = self.helper_retrieve_last_request_post_dict_key_val_index_zero_or_return_none("single_note_line_prepend_minus_space")

        task_id = self.woolnote_config.single_note_line_id[single_note_line_id]
        task = self.task_store.store_dict_id[task_id]

        contents_new_list = []
        contents_old = task.body
        for line in contents_old.split("\n"):
            if line.endswith(":#^#") and any((line.startswith("#^#:"), line.startswith("- #^#:"),
                                              line.startswith("+ #^#:"), line.startswith("* #^#:"),
                                              line.startswith("** #^#:"), line.startswith("*** #^#:"),
                                              line.startswith("**** #^#:") )):
                id = line.split("#^#:")[1].split(":#^#")[0]
                if id == single_note_line_id:
                    single_note_line_text_stripped = single_note_line_text.replace("\n", "").replace("\r", "").strip()
                    if single_note_line_prepend_minus_space:
                        single_note_line_text_stripped = "- " + single_note_line_text_stripped
                    if single_note_line_text_stripped:
                        contents_new_list.append(single_note_line_text_stripped)
            contents_new_list.append(line)

        self.ui_backend.helper_sanitize_task_body_before_save(task_to_be_updated=task,
                                                              tainted_task_body="\n".join(contents_new_list))

        self.ui_backend.save_edited_note(task)

        self.last_request_get_dict["taskid"] = [
            task.taskid]  # inject back so that the next rendered page can access it as if the note editing has been requested


    @tests.integration_method("web_ui")
    def req_save_new_note(self):
        """
        Saves a new note from the GET and POST data.

        Returns:
            None:
        """


        if self.helper_action_get_request_is_wrong("req_save_new_note"):
            return

        if self.helper_sessactionauth_is_wrong():
            return

        task = Task()

        self.helper_save_task_itself_from_req(task)

        self.ui_backend.save_new_note(task)
        self.last_request_get_dict["taskid"] = [
            task.taskid]  # inject back so that the next rendered page can access it as if the note always existed


    @tests.integration_method("web_ui")
    def req_save_edited_note(self):
        """
        Saves a new version of an existing note from the GET and POST data.

        Returns:
            None:
        """

        if self.helper_action_get_request_is_wrong("req_save_edited_note"):
            self.error_msg_queue_note.append("Note has not been saved.")
            return

        if self.helper_action_post_request_is_wrong("req_save_edited_note", "post_action"):
            # this POST value is not present when the page is visited from history
            # missing POST data and not doing this check would delete all checkboxes on the page
            self.error_msg_queue_note.append("Note has not been saved - wrong request (page reload?).")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_note.append("Note has not been saved - wrong session.")
            return

        # note: If the user changes the taskid value in the edit submit request to another existing note,
        #       that existing note is overwritten. This has to be intentional and taskids are long and
        #       random.
        task_id = util.sanitize_singleline_string_for_tasksave(self.last_request_get_dict["taskid"][0])
        task = self.task_store.store_dict_id[task_id]

        self.helper_save_task_itself_from_req(task)

        self.ui_backend.save_edited_note(task)

    @tests.integration_method("web_ui")
    def req_note_dismiss_reminder(self):
        """
        Marks the note's reminder attribute as dismissed so that it won't show up again (until the attribute is set to
        True by other code again) (gets the task id from GET).

        Returns:
            None:
        """
        if self.helper_action_get_request_is_wrong("req_dismiss_reminder_and_display_note"):
            self.error_msg_queue_note.append("Reminder has not been dismisses - application error?")
            return

        task_id = util.sanitize_singleline_string_for_tasksave(self.last_request_get_dict["taskid"][0])
        task = self.task_store.store_dict_id[task_id]

        # TODO move to backend?
        task.due_date_reminder_dismissed = True
        self.task_store.touch(task.taskid)
        self.task_store.task_store_save()

    @tests.integration_method("web_ui")
    def req_note_checkboxes_save(self):
        """
        Saves checkboxes for a note. Gets the required data from GET and POST. Has to get all checkboxes that are
        checked, the rest is automatically unchecked.
        Returns:
            None:
        """
        if self.helper_action_get_request_is_wrong("req_note_checkboxes_save"):
            self.error_msg_queue_note.append("Checkboxes were not saved.")
            return

        if self.helper_action_post_request_is_wrong("req_note_checkboxes_save", "post_action"):
            # this POST value is not present when the page is visited from history
            # missing POST data and not doing this check would delete all checkboxes on the page
            self.error_msg_queue_note.append("Checkboxes were not saved - wrong request (page reload?).")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_note.append("Checkboxes were not saved - wrong session.")
            return

        task_id = util.sanitize_singleline_string_for_tasksave(self.last_request_get_dict["taskid"][0])
        task = self.task_store.store_dict_id[task_id]

        hash_task_body_current = hashlib.sha256(repr(task.body).encode("utf-8")).hexdigest()
        hash_task_body_request = self.last_request_get_dict.get("task_body_hash", [""])[0]
        if hash_task_body_current != hash_task_body_request:
            self.error_msg_queue_note.append("Checkboxes were not saved - tried to save checkboxes for an older version of the note.")
            return

        # TODO move to backend?
        post_data_keys = list(self.last_request_post_data_dict.keys())
        cms_str = util.convert_multiline_markup_string_into_safe_html(task.body)
        new_task_body = util.multiline_markup_checkbox_mapping(cms_str, task.body, edit_chkbox_state=True,
                                                               chkbox_on_list=post_data_keys)

        task.body = new_task_body
        self.ui_backend.save_edited_note(task)


    @tests.integration_method("web_ui")
    def req_import_notes(self):
        """
        Imports notes (either by synchronization or by overwriting everything local). Doesn't save the result
        permanently until another operation calls task_store.task_store_save() (all data-changing operations do it and
        another launch of import would do it). Imports from the configured path.

        Returns:
            None:
        """

        if self.helper_action_get_request_is_wrong("req_import_notes"):
            self.error_msg_queue_list.append("Import not performed.")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_list.append("Import not performed - wrong session?")
            return

        user_supplied_nonce = self.last_request_get_dict["nonceactionauth"][0]
        if not self.check_one_time_nonce(user_supplied_nonce):
            self.error_msg_queue_list.append("Import not performed - page expired.")
            return

        replace_local_request = "yes" == self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("replace_local")

        self.error_msg_queue_list.append("Imported changes are only saved once a next permanent action is performed (saving a note, saving note checkboxes, exporting notes, deleting a note). If you are unhappy with the import operation and want to revert the import, kill/quit the woolnote server immediately.")
        ret = self.ui_backend.import_notes(replace_local_request)
        if ret is not None:
            self.error_msg_queue_list.append(ret)

    @tests.integration_method("web_ui")
    def req_export_notes(self):
        """
        Exports notes to the configured path.

        Returns:
            None:
        """

        if self.helper_action_get_request_is_wrong("req_export_notes"):
            self.error_msg_queue_list.append("Export not performed.")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_list.append("Export not performed - wrong session?")
            return

        user_supplied_nonce = self.last_request_get_dict["nonceactionauth"][0]
        if not self.check_one_time_nonce(user_supplied_nonce):
            self.error_msg_queue_list.append("Export not performed - page expired.")
            return

        self.ui_backend.export_notes()

    @tests.integration_method("web_ui")
    def req_delete_taskid(self):
        """
        Deletes the notes specified by the task ids from POST data. This is to be the final function to be called in
        the web ui in the process of deleting - this function doesn't ask for any confirmation.

        Returns:
            None:
        """
        if self.helper_action_get_request_is_wrong("req_delete_taskid"):
            self.error_msg_queue_list.append("Note deletion not performed.")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_list.append("Note deletion not performed - wrong session?")
            return

        task_id_list = self.last_request_post_data_dict["taskid"]
        self.ui_backend.delete_taskid(task_id_list)

    @tests.integration_method("web_ui")
    def req_note_list_manipulate_tagdel(self):
        """
        Deletes the tag specified in POST data from notes having the task ids specified in POST data.

        Returns:
            None:
        """
        if self.helper_action_get_request_is_wrong("req_note_list_manipulate_tagdel"):
            self.error_msg_queue_list.append("Note manipulation not performed.")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_list.append("Note manipulation not performed - wrong session?")
            return

        try:
            task_id_list = self.last_request_post_data_dict["taskid"]
            tagdel = self.last_request_post_data_dict["tagdel"][0]
        except:
            self.error_msg_queue_list.append("Note manipulation not performed - cannot access required POST data.")
        else:
            self.ui_backend.notes_tagdel(task_id_list, tagdel)

    @tests.integration_method("web_ui")
    def req_note_list_manipulate_tagadd(self):
        """
        Adds the tag specified in POST data to notes having the task ids specified in POST data.

        Returns:
            None:
        """

        if self.helper_action_get_request_is_wrong("req_note_list_manipulate_tagadd"):
            self.error_msg_queue_list.append("Note manipulation not performed.")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_list.append("Note manipulation not performed - wrong session?")
            return

        try:
            task_id_list = self.last_request_post_data_dict["taskid"]
            tagadd = self.last_request_post_data_dict["tagadd"][0]
        except:
            self.error_msg_queue_list.append("Note manipulation not performed - cannot access required POST data.")
        else:
            self.ui_backend.notes_tagadd(task_id_list, tagadd)

    @tests.integration_method("web_ui")
    def req_note_list_manipulate_foldermove(self):
        """
        Changes the folder specified in POST data for notes having the task ids specified in POST data.

        Returns:
            None:
        """

        if self.helper_action_get_request_is_wrong("req_note_list_manipulate_foldermove"):
            self.error_msg_queue_list.append("Note manipulation not performed.")
            return

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_list.append("Note manipulation not performed - wrong session?")
            return

        try:
            task_id_list = self.last_request_post_data_dict["taskid"]
            foldermove = self.last_request_post_data_dict["foldermove"][0]
        except:
            self.error_msg_queue_list.append("Note manipulation not performed - cannot access required POST data.")
        else:
            self.ui_backend.notes_foldermove(task_id_list, foldermove)

    @tests.integration_method("web_ui")
    def helper_get_task_or_default(self):
        """
        A helper function that either retrieves the requested task from the request or returns contents of a page
        that should be rendered when the task has not been found in the request.

        Returns:
            Union[Tuple[bool, str, woolnote.task_store.Task, str], Tuple[bool, int, int, str]]:
            1) bool - whether a task specified by "taskid" in request was found
            2) the taskid of the task, if found
            3) the task, if found
            4) the "not found" page that should be rendered if task not found
        """
        task_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("taskid")
        alt_task_store_name = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("alt_task_store_name")
        used_task_store = self.task_store
        # don't want to use sth like globals.get(alt_task_store) so that only approved stores can be used
        if alt_task_store_name == "task_store_trash":
            used_task_store = self.task_store_trash
        try:
            task = used_task_store.store_dict_id[task_id]
        except Exception as exc:
            # task_id is either None or it is not in store_dict_id
            util.dbgprint("exception in helper_get_task_or_default, semi-expected {}".format(str(exc)))
            self.error_msg_queue_list.append("Couldn't retrieve requested note.")
            return False, 0, 0, self.page_list_notes(no_history=True)
        return True, task_id, task, ""


    @tests.integration_method("web_ui")
    def page_edit_note(self):
        """
        Displays a note-editing page for an existing note whose task id is specified in GET data.

        Returns:
            str: html page contents to be displayed
        """

        task_found, task_id, task, notfound_page = self.helper_get_task_or_default()
        if not task_found:
            self.error_msg_queue_list.append("Cannot edit specified note.")
            return notfound_page

        history_back_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("history_back_id")

        page_header_list_of_warnings = None
        if self.error_msg_queue_note:
            page_header_list_of_warnings = self.helper_convert_msg_queue_note_to_list_for_output()

        page_body = html_page_templates.page_edit_note_template(self.task_store, task, self.sess_action_auth,
                                            editing_mode_existing_note=True, history_back_id=history_back_id,
                                            page_header_list_of_warnings=page_header_list_of_warnings)

        return page_body

    @tests.integration_method("web_ui")
    def page_add_new_note(self):
        """
        Displays a note-editing page for a new (yet nonexistent) note.

        Returns:
            str: html page contents to be displayed
        """

        history_back_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("history_back_id")

        task = Task()  # just a temporary one, won't even be saved; it's just so that the form below can stay unchanged

        page_body = html_page_templates.page_edit_note_template(self.task_store, task, self.sess_action_auth,
                                            editing_mode_existing_note=False, history_back_id=history_back_id)

        return page_body

    @tests.integration_method("web_ui")
    def unauth_page_display_note_public(self, tainted_task_id, tainted_task_pubauthid):
        """
        Displays a read-only note if the provided note-specific authentication tokens are right. This allows displaying
        notes without login. The GET data have to have the correct task id and the correct task pubauthid (supposed
        to be unique for every note but it is user-configurable). If the pubauthid is shorter than 5 characters, access
        is automatically denied even if it is correct.

        Args:
            tainted_task_id (str):
            tainted_task_pubauthid (str):

        Returns:
            str: html page contents to be displayed to the unauthenticated user

        Raises:
            Exception: when anything is not right, an exception is raised; the exception should be anticipated by the
                       caller because it is raised for every unauthorized access
        """

        if tainted_task_id is None:
            raise Exception("task_id==None")

        if tainted_task_pubauthid is None:
            raise Exception("task_pubauthid==None")

        task = self.task_store.store_dict_id[tainted_task_id]  # exception if not found
        if task is None:
            raise Exception("task==None")

        # too short strings are inherently insecure
        if len(task.public_share_auth) < 5:
            task.public_share_auth = util.create_id_task()
            raise Exception("task.public_share_auth insecure")

        # hashing&salting so that string comparison doesn't easily allow timing attacks
        if not util.safe_string_compare(task.public_share_auth, tainted_task_pubauthid):
            raise Exception("task_pubauthid=None")
        else:
            page_body = html_page_templates.unauth_page_display_note_public_template(
                tainted_task_id=tainted_task_id,
                tainted_task_pubauthid=tainted_task_pubauthid,
                task_store=self.task_store
            )

            return page_body

    @tests.integration_method("web_ui")
    def page_display_note(self):
        """
        Displays the note specified by task id in GET data. The page contains links to save checkboxes or to edit the
        note.

        Returns:
            str: html page contents to be displayed
        """

        task_found, task_id, task, notfound_page = self.helper_get_task_or_default()
        if not task_found:
            self.error_msg_queue_list.append("Cannot display specified note.")
            return notfound_page

        alt_task_store_name = self.helper_get_alt_task_store_name()

        highlight_in_text = None
        try:
            highlight_in_text = [x for x in self.last_request_get_dict["highlight_in_text"]]  # not sanitized
            util.dbgprint(highlight_in_text)
        except Exception as exc:
            util.dbgprint("expected exception ama {}".format(str(exc)))

        history_back_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("history_back_id")

        page_header_list_of_warnings = None
        if self.error_msg_queue_note:
            page_header_list_of_warnings = self.helper_convert_msg_queue_note_to_list_for_output()

        page_body = html_page_templates.page_display_note_template(
            task_id=task.taskid,
            task=task,
            page_header_optional_list_of_warnings=page_header_list_of_warnings,
            alt_task_store_name=alt_task_store_name,
            highlight_in_text=highlight_in_text,
            history_back_id=history_back_id,
            self_sess_action_auth=self.sess_action_auth,
        )

        return page_body

    @tests.integration_method("web_ui")
    def page_list_notes(self, no_history=False):
        """
        Displays a list of notes. The page contains links to existing folders, tags, virtual folders, other links, and
        contains a list of all existing notes. This is the main page of woolnote.

        Args:
            no_history (bool): If true, this invocation is not saved into history as a point where to go back to. To be
                               used when this method is called in an exception handler because saving the history would
                               save not the request to display a note list but to do whatever action that has just
                               thrown the exception.

        Returns:
            str: html page contents to be displayed
        """

        list_taskid_desc = self.task_store.sort_taskid_list_descending_lamport()
        title = "woolnote - all notes"
        page_header_first_text = "all notes"

        if no_history:
            history_id = self.save_history([])
        else:
            history_id = self.save_history(["action"], alt_task_store_name=None)

        page_header_list_of_warnings = None
        page_header_small_text = None

        if self.error_msg_queue_list:
            page_header_list_of_warnings = self.helper_convert_msg_queue_list_to_list_for_output()
        else:
            try:
                # TODO: use asn library?
                # sha256_fp = read_pem_cert_fingerprint(SSL_CERT_PEM_PATH)
                page_header_small_text = config.SSL_CERT_PEM_FINGERPRINT
            except:
                page_header_small_text = "cannot get ssl cert sha256"

        return html_page_templates.page_list_notes_template(list_taskid_desc=list_taskid_desc,
                                        self_sess_action_auth=self.sess_action_auth, title=title,
                                        history_back_id=history_id, primary_task_store=self.task_store,
                                        virtual_folders=self.woolnote_config.virtual_folders,
                                        single_task_line_ids=set(self.woolnote_config.single_note_line_id.keys()),
                                        page_header_first_text=page_header_first_text,
                                        page_header_optional_small_second_text=page_header_small_text,
                                        page_header_optional_list_of_warnings=page_header_list_of_warnings)

    @tests.integration_method("web_ui")
    def page_list_trash(self):
        """
        Displays a list of notes in the trash. The page is otherwise very similar to page_list_notes().

        Returns:
            str: html page contents to be displayed
        """

        list_taskid_desc = self.task_store_trash.sort_taskid_list_descending_lamport()
        title = "woolnote - trash"
        page_header_first_text = "notes in the trash"
        page_header_link_button_name = "reset filter"
        page_header_link_request_dict = {"action": "show_list"}
        page_header_list_of_warnings = None

        if self.error_msg_queue_list:
            page_header_list_of_warnings = self.helper_convert_msg_queue_list_to_list_for_output()

        history_id = self.save_history(["action"], alt_task_store_name=None)

        return html_page_templates.page_list_notes_template(list_taskid_desc=list_taskid_desc,
                                        self_sess_action_auth=self.sess_action_auth, title=title,
                                        primary_task_store=self.task_store, alt_task_store=self.task_store_trash,
                                        alt_task_store_name="task_store_trash", history_back_id=history_id,
                                        virtual_folders=self.woolnote_config.virtual_folders,
                                        single_task_line_ids=set(self.woolnote_config.single_note_line_id.keys()),
                                        page_header_first_text=page_header_first_text,
                                        page_header_optional_link_button_name=page_header_link_button_name,
                                        page_header_optional_link_button_request_dict=page_header_link_request_dict,
                                        page_header_optional_list_of_warnings=page_header_list_of_warnings)

    @tests.integration_method("web_ui")
    def page_search_notes(self):
        """
        Displays a list of notes matching the search_text provided in the GET data. The page is otherwise very similar
        to page_list_notes().

        Returns:
            str: html page contents to be displayed
        """

        task_store_name = "task_store"
        alt_task_store = None
        alt_task_store_name = self.helper_get_alt_task_store_name()
        if alt_task_store_name == "task_store_trash":
            task_store_name = alt_task_store_name
            alt_task_store = self.task_store_trash

        search_text = self.last_request_get_dict["search_text"][0].lower()
        list_taskid_desc, highlight_list = self.ui_backend.search_notes(task_store_name, search_text)

        # in the rest of the function, the variable should be None if it is the default task store
        if task_store_name == "task_store":
            task_store_name = None

        history_id = self.save_history(["search_text", "action"], alt_task_store_name=alt_task_store_name)

        title = "woolnote - search " + search_text

        page_header_first_text = "search " + search_text
        page_header_link_button_name = "reset filter"
        page_header_link_request_dict = {"action": "show_list"}
        page_header_list_of_warnings = None

        if self.error_msg_queue_list:
            page_header_list_of_warnings = self.helper_convert_msg_queue_list_to_list_for_output()

        return html_page_templates.page_list_notes_template(list_taskid_desc=list_taskid_desc,
                                        self_sess_action_auth=self.sess_action_auth, title=title,
                                        highlight_in_notes=highlight_list, primary_task_store=self.task_store,
                                        alt_task_store=alt_task_store, alt_task_store_name=alt_task_store_name,
                                        history_back_id=history_id,
                                        virtual_folders=self.woolnote_config.virtual_folders,
                                        single_task_line_ids=set(self.woolnote_config.single_note_line_id.keys()),
                                        page_header_first_text=page_header_first_text,
                                        page_header_optional_link_button_name=page_header_link_button_name,
                                        page_header_optional_link_button_request_dict=page_header_link_request_dict,
                                        page_header_optional_list_of_warnings=page_header_list_of_warnings)

    @tests.integration_method("web_ui")
    def page_list_folder(self):
        """
        Displays a list of notes in the folder specified in the GET data. The page is otherwise very similar
        to page_list_notes().

        Returns:
            str: html page contents to be displayed
        """


        alt_task_store_name = None
        alt_task_store = None
        try:
            alt_task_store_name = self.last_request_get_dict["alt_task_store_name"][0]
            if alt_task_store_name == "task_store_trash":
                alt_task_store = self.task_store_trash
            else:
                alt_task_store_name = None
                alt_task_store = None
        except Exception as exc:
            util.dbgprint("expected exception asa {}".format(str(exc)))
        used_task_store = self.task_store
        if alt_task_store:
            used_task_store = alt_task_store

        try:
            folder = self.last_request_get_dict["folder"][0]
            list_taskid_desc = used_task_store.filter_folder(folder)
        except Exception as exc:
            util.dbgprint("exception aoa, semi-expected {}".format(str(exc)))
            return self.page_list_notes(no_history=True)

        history_id = self.save_history(["folder", "action"], alt_task_store_name=alt_task_store_name)

        title = "woolnote - notes in " + folder

        page_header_first_text = "notes in " + folder
        page_header_link_button_name = "reset filter"
        page_header_link_request_dict = {"action": "show_list"}
        page_header_list_of_warnings = None

        if self.error_msg_queue_list:
            page_header_list_of_warnings = self.helper_convert_msg_queue_list_to_list_for_output()

        return html_page_templates.page_list_notes_template(list_taskid_desc=list_taskid_desc,
                                        self_sess_action_auth=self.sess_action_auth, title=title,
                                        primary_task_store=self.task_store, alt_task_store=alt_task_store,
                                        alt_task_store_name=alt_task_store_name, history_back_id=history_id,
                                        virtual_folders=self.woolnote_config.virtual_folders,
                                        single_task_line_ids=set(self.woolnote_config.single_note_line_id.keys()),
                                        page_header_first_text=page_header_first_text,
                                        page_header_optional_link_button_name=page_header_link_button_name,
                                        page_header_optional_link_button_request_dict=page_header_link_request_dict,
                                        page_header_optional_list_of_warnings=page_header_list_of_warnings)

    @tests.integration_method("web_ui")
    def page_list_tag(self):
        """
        Displays a list of notes in the tag specified in the GET data. The page is otherwise very similar to
        page_list_notes().

        Returns:
            str: html page contents to be displayed
        """


        alt_task_store_name = None
        alt_task_store = None
        try:
            alt_task_store_name = self.last_request_get_dict["alt_task_store_name"][0]
            if alt_task_store_name == "task_store_trash":
                alt_task_store = self.task_store_trash
            else:
                alt_task_store_name = None
                alt_task_store = None
        except Exception as exc:
            util.dbgprint("expected exception asa {}".format(str(exc)))
        used_task_store = self.task_store
        if alt_task_store:
            used_task_store = alt_task_store

        try:
            tag = self.last_request_get_dict["tag"][0]
            list_taskid_desc = used_task_store.filter_tag(tag)
        except Exception as exc:
            util.dbgprint("exception apa, semi-expected {}".format(str(exc)))
            return self.page_list_notes(no_history=True)

        history_id = self.save_history(["tag", "action"], alt_task_store_name=alt_task_store_name)

        title = "woolnote - notes in " + tag

        page_header_first_text = "notes in " + tag
        page_header_link_button_name = "reset filter"
        page_header_link_request_dict = {"action": "show_list"}
        page_header_list_of_warnings = None

        if self.error_msg_queue_list:
            page_header_list_of_warnings = self.helper_convert_msg_queue_list_to_list_for_output()

        return html_page_templates.page_list_notes_template(list_taskid_desc=list_taskid_desc,
                                        self_sess_action_auth=self.sess_action_auth, title=title,
                                        primary_task_store=self.task_store, alt_task_store=alt_task_store,
                                        alt_task_store_name=alt_task_store_name, history_back_id=history_id,
                                        virtual_folders=self.woolnote_config.virtual_folders,
                                        single_task_line_ids=set(self.woolnote_config.single_note_line_id.keys()),
                                        page_header_first_text=page_header_first_text,
                                        page_header_optional_link_button_name=page_header_link_button_name,
                                        page_header_optional_link_button_request_dict=page_header_link_request_dict,
                                        page_header_optional_list_of_warnings=page_header_list_of_warnings)

    @tests.integration_method("web_ui")
    def page_note_list_multiple_select(self):
        """
        Displays a list of actions and list of selected notes on which the actions can be performed.

        Returns:
            str: html page contents to be displayed
        """

        tasks_to_delete = []
        try:
            list_taskid_desc_unfiltered = self.task_store.sort_taskid_list_descending_lamport()
            post_data_keys = list(self.last_request_post_data_dict.keys())
            for taskid in list_taskid_desc_unfiltered:
                task = self.task_store.store_dict_id[taskid]
                if taskid in post_data_keys:
                    tasks_to_delete.append(task)
        except Exception as exc:
            util.dbgprint("exception aqa, semi-expected {}".format(str(exc)))
            self.error_msg_queue_list.append("Cannot get the list of notes for multi-select manipulation.")
            return self.page_list_notes(no_history=True)

        history_back_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("history_back_id")

        page_body = html_page_templates.page_note_list_multiple_select_template(
            tasks_to_delete=tasks_to_delete,
            task_store=self.task_store,
            history_back_id=history_back_id,
            self_sess_action_auth=self.sess_action_auth
        )
        return page_body

    @tests.integration_method("web_ui")
    def page_delete_notes(self):
        """
        Displays a list of notes to delete with a red button deleting them for good and a cancel button.

        Returns:
            str: html page contents to be displayed
        """

        if self.helper_sessactionauth_is_wrong():
            self.error_msg_queue_list.append("Cannot display note deletion page - wrong session?")
            return self.page_list_notes(no_history=True)

        tasks_to_delete = []
        try:
            delete_taskid_list = self.last_request_post_data_dict["taskid"]
            for taskid, task in self.task_store.store_dict_id.items():
                if taskid in delete_taskid_list:
                    tasks_to_delete.append(task)
        except:
            # util.dbgprint("delete_notes_page_page() - no post data detected")
            # get get data instead
            try:
                delete_taskid_list = self.last_request_get_dict["taskid"]
                for taskid, task in self.task_store.store_dict_id.items():
                    if taskid in delete_taskid_list:
                        tasks_to_delete.append(task)
            except Exception as exc:
                util.dbgprint("exception ara, semi-expected {}".format(str(exc)))
                self.error_msg_queue_list.append("Cannot display note deletion page - wrong request?")
                return self.page_list_notes(no_history=True)

        history_back_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("history_back_id")

        page_body = html_page_templates.page_delete_notes_template(
            tasks_to_delete=tasks_to_delete,
            history_back_id=history_back_id,
            self_sess_action_auth=self.sess_action_auth
        )

        return page_body

    @tests.integration_method("web_ui")
    def page_export_prompt(self):
        """
        Displays a question whether to export notes into the configured path.

        Returns:
            str: html page contents to be displayed
        """

        nonce = self.create_new_nonce()
        history_back_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("history_back_id")

        page_body = html_page_templates.page_export_prompt_template(
            nonce=nonce,
            history_back_id=history_back_id,
            self_sess_action_auth=self.sess_action_auth,
        )
        return page_body

    @tests.integration_method("web_ui")
    def page_import_prompt(self):
        """
        Displays a question whether to import notes from the configured path. Two types of import are offered - sync
        import and plain overwrite import.

        Returns:
            str: html page contents to be displayed
        """

        nonce = self.create_new_nonce()
        history_back_id = self.helper_retrieve_last_request_get_dict_key_val_index_zero_or_return_none("history_back_id")

        page_body = html_page_templates.page_import_prompt_template(
            nonce=nonce,
            history_back_id=history_back_id,
            self_sess_action_auth=self.sess_action_auth,
        )
        return page_body

    def edit_folders_page(self):
        # TODO - shows a list of folders with links to edit them
        pass

    def edit_tags_page(self):
        # TODO - shows a list of tags with links to edit them
        pass

    def edit_folder_page(self):
        # TODO - shows a selected folder to edit and allows renaming or deleting
        pass

    def edit_tag_page(self):
        # TODO - shows a selected tag to edit and allows renaming or deleting
        pass
