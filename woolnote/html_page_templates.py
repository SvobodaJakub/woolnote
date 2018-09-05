# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

# TODO: docstring for the file
import hashlib
import os
from woolnote import systemencoding


from woolnote import util
from woolnote import html_page_templates_pres
from woolnote import config
from woolnote import tests



@tests.integration_function("html_page_templates")
def folder_tag_etc_list(action_name, req_elem_name, elem_list=None, elem_dict=None, sort_elem_list=False,
                                      sorted_tuple_list=None, small_text=False, alt_task_store_name=None,
                                      red_bold_text=False):
    """
    Generates a list of links to actions based on a list of elements leading to these actions.
    If a dictionary instead of a list is supplied, the generated requests contain the values of the keys
    while the user-visible strings in the links are the dictionary keys.
    If both elem_list and elem_dict are provided, the elem_list is iterated over (instead of elem_dict.keys()),
    so that it is possible to define the order.
    If sorted_tuple_list is provided, elem_list, elem_dict, and sort_elem_list are ignored.

    Args:
        action_name (str): value for the "action" request key
        req_elem_name (str): the key name for the request (value is the individual element)
        elem_list (Union[List[str], None]): list of elements (tag names, folder names, ...) for which to generate links
        elem_dict (Union[None, Dict[str, str]]): dict where keys are the names of elements to display in the links (tag names, ...) and values are the requests to use in the link address
        sort_elem_list (bool): whether to sort the user-visible elements (tags, folders, ...)
        sorted_tuple_list (Union[None, List[Tuple[str, str]]]): sorted tuples (display_elem_name, request_value) for the individual elements
        small_text (bool): whether to display the user-visible links as small text
        alt_task_store_name (Union[None, str]): if not None, it is added to the links so that the links point to the right task store
        red_bold_text (bool): If True, the text is bold and red

    Returns:
        List[woolnote.html_page_templates_pres.FormattedLinkData]: list of objects that return html links
    """
    ss = util.sanitize_singleline_string_for_html
    elem_list_data_for_html_fragment_list = []


    if sorted_tuple_list is None:  # specifically testing for None, not for emptiness
        sorted_tuple_list = []
        if elem_dict and not elem_list:
            elem_list = elem_dict.keys()
        if sort_elem_list:
            elem_list = sorted(elem_list)
        for elem in elem_list:
            req_value = elem
            if elem_dict:
                req_value = elem_dict[elem]
            sorted_tuple_list.append((elem, req_value))
    for elem, req_value in sorted_tuple_list:
        curr_elem = html_page_templates_pres.FormattedLinkData()
        curr_elem.request_params_dict = {"action": action_name, req_elem_name: req_value}
        if alt_task_store_name:
            curr_elem.request_params_dict.update({"alt_task_store_name": alt_task_store_name})
        if small_text:
            curr_elem.small = True
        else:
            curr_elem.small = False
        if red_bold_text:
            curr_elem.red_bold = True
        else:
            curr_elem.red_bold = False
        curr_elem.link_display_text = elem
        elem_list_data_for_html_fragment_list.append(curr_elem)
    return elem_list_data_for_html_fragment_list


@tests.integration_function("html_page_templates")
def generate_note_reminder_link_list_html_fragment(list_taskid, used_task_store, overdue=False,
                                                   alt_task_store_name=None, dismiss_reminder_action=False):
    """
    Generates a list of links to notes that have a due date set. If overdue=False, then only the notes that
    are NOT overdue are displayed. If overdue=True, then only the notes that ARE overdue are displayed.
    The result is a HTML series of links to the notes.

    Args:
        list_taskid (List[str]): List of the task IDs from which the link list should be generated.
        used_task_store (woolnote.task_store.TaskStore): TaskStore where task IDs are searched.
        overdue (bool): If True, only the overdue are generated, if False, only the not-yet-overdue are generated.
        alt_task_store_name (Union[None, str]): if not None, it is added to the links so that the links point to the right task store
        dismiss_reminder_action (bool): If True, the generated link is colorful and bold and leads to the action dismiss_reminder_and_display_note

    Returns:
        List[woolnote.html_page_templates_pres.FormattedLinkData]: list of objects that return html links
    """
    reminder_set = set()
    current_date = util.current_timestamp()
    for taskid in list_taskid:
        task = used_task_store.store_dict_id[taskid]
        if task.due_date:
            if overdue:
                condition = task.due_date < current_date
            else:
                condition = task.due_date > current_date
            if condition and not (dismiss_reminder_action and task.due_date_reminder_dismissed):
                # (skip tasks which have been already dismissed if creating a list of reminders to dismiss
                reminder_set.add((task.due_date, task))
    sorted_tuples = sorted(reminder_set, key=lambda x: x[0])
    sorted_tuple_list = []
    for due_date, task in sorted_tuples:
        req_value = task.taskid
        elem_name = task.name + " - " + task.due_date
        sorted_tuple_list.append((elem_name, req_value))
    red_bold_text = False
    action_name="page_display_note"
    if overdue:
        small_text = False
    else:
        small_text = True
    if dismiss_reminder_action:
        red_bold_text = True
        action_name="req_dismiss_reminder_and_display_note"
    list_html_fragment = folder_tag_etc_list(
        action_name=action_name,
        req_elem_name="taskid",
        sorted_tuple_list=sorted_tuple_list,
        small_text=small_text,
        alt_task_store_name=alt_task_store_name,
        red_bold_text=red_bold_text
    )

    return list_html_fragment


@tests.integration_function("html_page_templates")
def page_edit_note_template(task_store, task, self_sess_action_auth,
                            editing_mode_existing_note=False, history_back_id=None, page_header_list_of_warnings=None):
    """
    Template for note editing - for creating a new note or editing an existing one.
    editing_mode_existing_note - False = editing mode for a new note, True = editing mode for an existing note
    (this controls which request the save button generates and which links are displayed)

    Args:
        task_store (woolnote.task_store.TaskStore):
        task (woolnote.task_store.Task):
        self_sess_action_auth (str):
        editing_mode_existing_note (bool): false == editing mode for a new note, true == editing mode for an existing note
        history_back_id (str):
        page_header_list_of_warnings (Union[None, list[str]]):

    Returns:
        Union[str, None]:
    """

    if editing_mode_existing_note:
        page = html_page_templates_pres.PageEditExistingData()
    else:
        page = html_page_templates_pres.PageEditNewData()
    page.task_name = task.name
    page.folder_list = task_store.get_folder_list()
    page.tag_list = task_store.get_tag_list()
    page.task_tags = task.tags
    page.task_folder = task.folder
    page.task_body_format = task.body_format
    page.task_body = task.body
    page.task_public_share_auth = task.public_share_auth
    page.task_taskid = task.taskid
    page.task_due_date = task.due_date
    page.sess_action_auth = self_sess_action_auth
    page.history_back_id = history_back_id
    page.page_header_list_of_warnings = page_header_list_of_warnings

    page_html = page.to_html()
    return page_html

# TODO
# TODO @tests.integration_function("html_page_templates")
def page_list_singleline_tasks_template(single_line_tasks_desc, self_sess_action_auth, title=None,
                             highlight_in_notes=None,
                             history_back_id=None,
                             page_header_first_text=None,
                             page_header_optional_small_second_text=None,
                             page_header_optional_link_button_name=None,
                             page_header_optional_link_button_request_dict=None,
                             page_header_optional_list_of_warnings=None):
    # TODO new docstring
    """
    Template for note list. The given list of taskids must be matchable with the given task store. Both the reference
    to the task store and the name of the task store must be given (internal details and hardcoded task store names,
    search the code for more info).

    Args:
        single_line_tasks_desc (List[List[Tuple[str, str, str]]]): one nonempty list of tuples for each task, each tuple contains taskid, task_name, shasum, line.
        self_sess_action_auth (str):
        title (str):
        highlight_in_notes (Union[None, List[str]]): text to highlight in the notes listed on this page (after a note is opened)
        history_back_id (str): string returned by woolnote.web_ui.save_history()
        page_header_first_text (str):
        page_header_optional_small_second_text (Union[str, None]):
        page_header_optional_link_button_name (Union[str, None]):
        page_header_optional_link_button_request_dict (Union[None, Dict[str, str]]):
        page_header_optional_list_of_warnings (Union[List[str], None]):

    Returns:
        str:
    """

    page = html_page_templates_pres.PageOneLineTasks()
    page.page_title = title
    page.highlight_in_notes = highlight_in_notes
    page.sess_action_auth = self_sess_action_auth
    page.history_back_id = history_back_id
    page.page_header_first_text = page_header_first_text
    page.page_header_optional_small_second_text = page_header_optional_small_second_text
    page.page_header_optional_link_button_name = page_header_optional_link_button_name
    page.page_header_optional_link_button_request_dict = page_header_optional_link_button_request_dict
    page.page_header_optional_list_of_warnings = page_header_optional_list_of_warnings

    ll = []
    for list_of_tuple in single_line_tasks_desc:
        l = []
        for line in list_of_tuple:
            tld = page.TaskLineDetails(taskid=line[0], task_name=line[1], shasum=line[2], line=line[3])
            l.append(tld)
        ll.append(l)
    page.list_of_list_of_task_line_details = ll

    return page.to_html()



@tests.integration_function("html_page_templates")
def page_list_notes_template(list_taskid_desc, self_sess_action_auth, title=None, primary_task_store=None,
                             alt_task_store=None, alt_task_store_name=None, highlight_in_notes=None,
                             history_back_id=None, virtual_folders=None, single_task_line_ids=None,
                             page_header_first_text=None,
                             page_header_optional_small_second_text=None,
                             page_header_optional_link_button_name=None,
                             page_header_optional_link_button_request_dict=None,
                             page_header_optional_2nd_link_button_name=None,
                             page_header_optional_2nd_link_button_request_dict=None,
                             page_header_optional_list_of_warnings=None):
    """
    Template for note list. The given list of taskids must be matchable with the given task store. Both the reference
    to the task store and the name of the task store must be given (internal details and hardcoded task store names,
    search the code for more info).

    Args:
        list_taskid_desc (List[str]): notes are listed in the order of taskids
        self_sess_action_auth (str):
        title (str):
        primary_task_store (woolnote.task_store.TaskStore): Always give the reference to the primary task store.
        alt_task_store (Union[None, woolnote.task_store.TaskStore]): If the notes should be listed from a different task store (e.g. trash), give the reference to it, otherwise None.
        alt_task_store_name (Union[None, str]): If alt_task_store==None, set this also to None; otherwise specify the internal hardcoded task store name (e.g. task_store_trash).
        highlight_in_notes (Union[None, List[str]]): text to highlight in the notes listed on this page (after a note is opened)
        history_back_id (str): string returned by woolnote.web_ui.save_history()
        virtual_folders (Dict[str, str]): woolnote.woolnote_config.virtual_folders
        single_task_line_ids (Set[str]): woolnote.woolnote_config.single_note_line_id.keys()
        page_header_first_text (str):
        page_header_optional_small_second_text (Union[str, None]):
        page_header_optional_link_button_name (Union[str, None]):
        page_header_optional_link_button_request_dict (Union[None, Dict[str, str]]):
        page_header_optional_2nd_link_button_name (Union[str, None]):
        page_header_optional_2nd_link_button_request_dict (Union[None, Dict[str, str]]):
        page_header_optional_list_of_warnings (Union[List[str], None]):

    Returns:
        str:
    """

    page = html_page_templates_pres.PageListData()
    page.page_title = title
    page.alt_task_store_name = alt_task_store_name
    page.highlight_in_notes = highlight_in_notes
    page.sess_action_auth = self_sess_action_auth
    page.history_back_id = history_back_id
    page.page_header_first_text = page_header_first_text
    page.page_header_optional_small_second_text = page_header_optional_small_second_text
    page.page_header_optional_link_button_name = page_header_optional_link_button_name
    page.page_header_optional_link_button_request_dict = page_header_optional_link_button_request_dict
    page.page_header_optional_2nd_link_button_name = page_header_optional_2nd_link_button_name
    page.page_header_optional_2nd_link_button_request_dict = page_header_optional_2nd_link_button_request_dict
    page.page_header_optional_list_of_warnings = page_header_optional_list_of_warnings


    used_task_store = primary_task_store
    if alt_task_store is not None:
        used_task_store = alt_task_store

    task_list_task_details_list = []
    for taskid in list_taskid_desc:
        task = used_task_store.store_dict_id[taskid]

        # simple data structures for rendering, no hidden logic (like in the case of Task instances)
        task_details = html_page_templates_pres.PageListData.TaskDetails(
            task_taskid=task.taskid,
            task_due_date=task.due_date,
            task_name=task.name,
            task_folder=task.folder,
            task_tags=task.tags,
            task_body=task.body
        )

        task_list_task_details_list.append(task_details)

    page.list_of_task_details = task_list_task_details_list


    page.folder_list = folder_tag_etc_list(
                action_name="page_list_folder",
                req_elem_name="folder",
                elem_list=used_task_store.get_folder_list(),
                alt_task_store_name=alt_task_store_name
            )


    page.tag_list = folder_tag_etc_list(
                action_name="page_list_tag",
                req_elem_name="tag",
                elem_list=used_task_store.get_tag_list(),
                alt_task_store_name=alt_task_store_name
            )

    page.virtfldr_list = folder_tag_etc_list(
                action_name="page_search_notes",
                req_elem_name="search_text",
                elem_dict=virtual_folders,
                sort_elem_list=True,
                alt_task_store_name=alt_task_store_name
            )

    page.single_note_line_id = single_task_line_ids

    page.context_list = folder_tag_etc_list(
                action_name="page_search_notes",
                req_elem_name="search_text",
                elem_list=used_task_store.get_context_list(),
                alt_task_store_name=alt_task_store_name
            )

    if alt_task_store is None:
        page.overdue_reminder_list = generate_note_reminder_link_list_html_fragment(
            list_taskid_desc, used_task_store, overdue=True, dismiss_reminder_action=True
        )

    page.overdue_list = generate_note_reminder_link_list_html_fragment(list_taskid_desc, used_task_store,
                                                           overdue=True,
                                                           alt_task_store_name=alt_task_store_name)

    page.reminder_list = generate_note_reminder_link_list_html_fragment(list_taskid_desc, used_task_store,
                                                           overdue=False,
                                                           alt_task_store_name=alt_task_store_name)


    return page.to_html()


@tests.integration_function("html_page_templates")
def unauth_page_display_note_public_template(tainted_task_id, tainted_task_pubauthid, task_store):
    """
    Displays a given task if the given parameters are correct. Meant to display a read-only note (so that the user
     can share a link that works without login). Extreme caution necessary.
    Args:
        tainted_task_id (str):
        tainted_task_pubauthid (str):
        task_store (woolnote.task_store.TaskStore):

    Returns:
        str:
    """

    if tainted_task_id is None:
        raise Exception("task_id==None")

    if tainted_task_pubauthid is None:
        raise Exception("task_pubauthid==None")

    task = task_store.store_dict_id[tainted_task_id]
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
        task_name = task.name
        task_body = task.body

        page = html_page_templates_pres.PageUnauthDisplayNoteData()
        page.task_body = task_body
        page.task_name = task_name
        return page.to_html()


@tests.integration_function("html_page_templates")
def page_display_note_template(task_id, task, page_header_optional_list_of_warnings=None,
                               alt_task_store_name=None, highlight_in_text=None, history_back_id=None,
                               self_sess_action_auth=None):
    """
    Template for displaying a single note.

    Args:
        task_id (str):
        task (woolnote.task_store.Task):
        page_header_optional_list_of_warnings (Union[None, str]):
        alt_task_store_name (Union[None, str]): If task is not from the primary store, specify the internal hardcoded task store name (e.g. task_store_trash).
        highlight_in_text (Union[None, list[str]]): text to highlight in the note (list of strings to highlight)
        history_back_id (Union[None, str]): string returned by woolnote.web_ui.save_history()
        self_sess_action_auth (str): woolnote.web_ui.WebUI.sess_action_auth

    Returns:
        str:
    """

    page = html_page_templates_pres.PageDisplayNoteData()

    page.task_id = task_id
    page.page_header_optional_list_of_warnings = page_header_optional_list_of_warnings
    page.alt_task_store_name = alt_task_store_name
    page.highlight_in_text = highlight_in_text
    page.history_back_id = history_back_id
    page.self_sess_action_auth = self_sess_action_auth

    page.task_text_formatting = task.body_format
    page.task_taskid = task.taskid
    page.task_due_date = task.due_date
    page.task_name = task.name
    page.task_folder = task.folder
    page.task_tags = task.tags
    page.task_body = task.body
    page.task_body_hash = hashlib.sha256(repr(task.body).encode("utf-8")).hexdigest()
    page.task_created_date = task.created_date
    page.task_changed_date = task.changed_date
    return page.to_html()


@tests.integration_function("html_page_templates")
def page_note_list_multiple_select_template(tasks_to_delete=None, task_store=None,
                                   history_back_id=None, self_sess_action_auth=None):
    """
    Shows a page with a list of tasks to manipulate.

    Args:
        tasks_to_delete (List[woolnote.task_store.Task]):
        task_store (woolnote.task_store.TaskStore):
        history_back_id (Union[None, str]): string returned by woolnote.web_ui.save_history()
        self_sess_action_auth (str): woolnote.web_ui.WebUI.sess_action_auth

    Returns:
        str:
    """


    task_details_to_delete = []
    for task in tasks_to_delete:
        # simple data structures for rendering, no hidden logic (like in the case of Task instances)
        task_details = html_page_templates_pres.PageMultipleSelectData.TaskDetails(
            task_taskid=task.taskid,
            task_due_date=task.due_date,
            task_name=task.name,
            task_folder=task.folder,
            task_tags=task.tags,
            task_body=task.body
        )
        task_details_to_delete.append(task_details)


    page = html_page_templates_pres.PageMultipleSelectData()
    page.folder_list = task_store.get_folder_list()
    page.tag_list = task_store.get_tag_list()
    page.task_details_to_delete = task_details_to_delete
    page.history_back_id = history_back_id
    page.self_sess_action_auth = self_sess_action_auth

    return page.to_html()


@tests.integration_function("html_page_templates")
def page_delete_notes_template(tasks_to_delete=None, history_back_id=None, self_sess_action_auth=None):
    """
    Template for a page with a list of tasks to delete. Upon confirmation, these tasks will be moved from task_store into
    task_store_trash (hardcoded).

    Args:
        tasks_to_delete (List[woolnote.task_store.Task]):
        history_back_id (Union[None, str]): string returned by woolnote.web_ui.save_history()
        self_sess_action_auth (str): woolnote.web_ui.WebUI.sess_action_auth

    Returns:
        str:
    """


    page = html_page_templates_pres.PageDeleteNotesData()

    task_details_to_delete = []
    for task in tasks_to_delete:
        # simple data structures for rendering, no hidden logic (like in the case of Task instances)
        task_details = html_page_templates_pres.PageDeleteNotesData.TaskDetails(
            task_taskid=task.taskid,
            task_due_date=task.due_date,
            task_name=task.name,
            task_folder=task.folder,
            task_tags=task.tags,
            task_body=task.body
        )
        task_details_to_delete.append(task_details)

    page.task_details_to_delete = task_details_to_delete
    page.history_back_id = history_back_id
    page.self_sess_action_auth = self_sess_action_auth

    return page.to_html()


@tests.integration_function("html_page_templates")
def page_export_prompt_template(nonce, history_back_id=None, self_sess_action_auth=None):
    """
    Template for a page with a button to export tasks.

    Args:
        nonce (str): string returned by woolnote.web_ui.create_new_nonce()
        history_back_id (Union[None, str]): string returned by woolnote.web_ui.save_history()
        self_sess_action_auth (str): woolnote.web_ui.WebUI.sess_action_auth

    Returns:
        str:
    """

    page = html_page_templates_pres.PageExportPromptData()
    page.nonce = nonce
    page.history_back_id = history_back_id
    page.self_sess_action_auth = self_sess_action_auth
    page.export_path = str(os.path.join(config.PATH_SAVE_DROPBOX_EXPORT, config.FILE_WOOLNOTE_ZIP))
    return page.to_html()


@tests.integration_function("html_page_templates")
def page_import_prompt_template(nonce, history_back_id=None, self_sess_action_auth=None):
    """
    Template for a page with a button to import tasks.

    Args:
        nonce (str): string returned by woolnote.web_ui.create_new_nonce()
        history_back_id (Union[None, str]): string returned by woolnote.web_ui.save_history()
        self_sess_action_auth (str): woolnote.web_ui.WebUI.sess_action_auth

    Returns:
        str:
    """

    page = html_page_templates_pres.PageImportPromptData()
    page.nonce = nonce
    page.history_back_id = history_back_id
    page.self_sess_action_auth = self_sess_action_auth
    page.import_path = str(os.path.join(config.PATH_LOAD_DROPBOX_IMPORT, config.FILE_WOOLNOTE_ZIP))
    return page.to_html()





