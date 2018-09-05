# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

# TODO: docstring for the file
from woolnote import systemencoding
import os
import copy
import zipfile
from woolnote import config
from woolnote import util
from woolnote.task_store import Task, TaskStore, MARKUP, PLAIN


# UI backend
############

class UIBackend():

    def __init__(self, task_store, task_store_trash):
        """
        Class holding references to the opened default and trash task stores and allowing UI-centric operations to be
        performed. The operations are not tied to any particular type of UI.

        Args:
            task_store (woolnote.task_store.TaskStore):
            task_store_trash (woolnote.task_store.TaskStore):
        """
        super().__init__()
        self.task_store = task_store
        self.task_store_trash = task_store_trash


    def helper_sanitize_task_body_before_save(self, task_to_be_updated, tainted_task_body):
        """
        Sanitizes new body of a task and saves it into the task.

        Args:
            task_to_be_updated (woolnote.task_store.Task):
            tainted_task_body (str):

        Returns:
            None:
        """

        # TODO: if the new body contains the delimiter used by the saved file in a vulnerable way, escape/remove it (don't do it here, do it in task_store.py)
        if task_to_be_updated.body_format == MARKUP:
            task_to_be_updated.body = util.task_body_save_fix_multiline_markup_bullet_lists(tainted_task_body)
        else:
            task_to_be_updated.body = util.task_body_save_fix_newlines(tainted_task_body)


    def helper_sanitize_task_before_save(self, task_to_be_updated,
                                         tainted_task_name,
                                         tainted_task_folder,
                                         tainted_task_pubauthid,
                                         tainted_task_tags,
                                         tainted_task_body,
                                         tainted_due_date,
                                         tainted_formatting):
        """
        Reads data for a new/saved note from POST data, performs sanitization, and correctly saves the data to a note
        (that also entails resetting the reminder flag if due date changes, correctly processing body text based on
        formatting used, setting the correct values for the formatting property). The data are saved into the provided
        task_to_be_updated but that task is not saved into a task store (you have to do that using a different function
        afterwards).

        Args:
            task_to_be_updated (woolnote.task_store.Task):
            tainted_task_name (str):
            tainted_task_folder (str):
            tainted_task_pubauthid (str):
            tainted_task_tags (str):
            tainted_task_body (str):
            tainted_due_date (str):
            tainted_formatting (str):

        Returns:
            None:
        """
        # TODO: can this be broken by other unicode newline characters?

        if tainted_task_tags.endswith(", "):
            tainted_task_tags = tainted_task_tags[:-2]

        task_to_be_updated.name = util.sanitize_singleline_string_for_tasksave(tainted_task_name)
        task_to_be_updated.folder = util.sanitize_singleline_string_for_tasksave(tainted_task_folder)
        task_to_be_updated.tags = {util.sanitize_singleline_string_for_tasksave(x) for x in tainted_task_tags.split(",")}

        old_due_date = task_to_be_updated.due_date
        task_to_be_updated.due_date = util.sanitize_singleline_string_for_tasksave(tainted_due_date)
        if old_due_date != task_to_be_updated.due_date:
            # when due date changes, the note is again ready to display a red reminder
            task_to_be_updated.due_date_reminder_dismissed = False

        task_to_be_updated.public_share_auth = util.sanitize_singleline_string_for_tasksave(tainted_task_pubauthid)
        # too short strings are inherently insecure
        if len(task_to_be_updated.public_share_auth) < 5:
            task_to_be_updated.public_share_auth = util.create_id_task()

        if tainted_formatting == "markup":
            task_to_be_updated.body_format = MARKUP
        elif tainted_formatting == "plaintext":
            task_to_be_updated.body_format = PLAIN
        else:
            # keeping unchanged, shouldn't happen
            util.dbgprint("tainted_formatting had a nonstandard value {}".format(tainted_formatting))
            pass

        self.helper_sanitize_task_body_before_save(task_to_be_updated=task_to_be_updated,
                                                   tainted_task_body=tainted_task_body)

    def save_new_note(self, task):
        """
        Saves a new task into the task store. That is, a task whose taskid is not already in the task store.
        Args:
            task (woolnote.task_store.Task):

        Returns:
            None:
        """
        self.task_store.add(task)
        self.task_store.task_store_save()

    def save_edited_note(self, task):
        """
        Saves a new version of an existing task into a task store. That is, a task whose taskid is already in the task store.
        Args:
            task (woolnote.task_store.Task):

        Returns:
            None:
        """
        task.changed_date = util.current_timestamp()
        self.task_store.touch(task.taskid)
        self.task_store.task_store_save()

    def import_notes(self, replace_local_request):
        """

        Imports notes from the configured path into the task store. Does either differential sync or overwrite all import
        depending on the argument.

        Args:
            replace_local_request (bool): If replace_local_request == True, then the remote database simply replaces the local database.

        Returns:
            Union[str, None]: error message or None if no error
        """

        self.task_store.task_store_save()
        self.task_store_trash.task_store_save()

        util.tasks_backup(self.task_store, self.task_store_trash, s="imp0")

        # import the zip into the local directory so that it can be loaded
        with zipfile.ZipFile(os.path.join(config.PATH_LOAD_DROPBOX_IMPORT, config.FILE_WOOLNOTE_ZIP), "r") as importzip:
            importzip.extract(config.FILE_WOOLNOTE_DAT, config.PATH_SAVE_DB)  # overwrites

        use_task_store = self.task_store
        use_task_store_trash = self.task_store_trash
        use_task_remote_store = TaskStore(os.path.join(config.PATH_SAVE_DB, config.FILE_WOOLNOTE_DAT))
        use_task_remote_store.task_store_load()

        if replace_local_request:
            use_task_store.store_dict_id = {}
            use_task_store.task_store_load(alt_path=os.path.join(config.PATH_SAVE_DB, config.FILE_WOOLNOTE_DAT))
            use_task_store.update_lamport_clock(use_task_remote_store.export_lamport_clock)
            use_task_store.last_import_lamport_clock = use_task_store.lamport_clock
            return None

        if use_task_remote_store.last_import_lamport_clock < use_task_store.export_lamport_clock:
            # if the remote store is based on an older export than the last export of the local store, abort the operation
            # (bad stuff might happen when importing such files)
            error_message = "Cannot import - internal database export lamport clock = {}, external database last import lamport clock = {}. ".format(
                str(int(use_task_store.export_lamport_clock)),
                str(int(use_task_remote_store.last_import_lamport_clock)))
            return error_message

        use_task_store.update_lamport_clock(use_task_remote_store.export_lamport_clock)
        use_task_store.last_import_lamport_clock = use_task_store.lamport_clock

        def local_change(task_local):
            # util.dbgprint("def local_change(task_local):")
            # util.dbgprint(task_local.lamport_timestamp > task_local.export_lamport_timestamp)
            return task_local.lamport_timestamp > task_local.export_lamport_timestamp

        def remote_change(task_local, task_remote):
            # util.dbgprint("def remote_change(task_local, task_remote):")
            # util.dbgprint(task_local.export_lamport_timestamp < task_remote.lamport_timestamp)
            return task_local.export_lamport_timestamp < task_remote.lamport_timestamp

        def no_change(task_local, task_remote):
            # util.dbgprint("def no_change(task_local, task_remote):")
            # util.dbgprint(((local_change(task_local) == False) and (remote_change(task_local, task_remote) == False)))
            return ((local_change(task_local) == False) and (remote_change(task_local, task_remote) == False))

        def both_change(task_local, task_remote):
            # util.dbgprint("def both_change(task_local, task_remote):")
            # util.dbgprint((local_change(task_local) and remote_change(task_local, task_remote)))
            return (local_change(task_local) and remote_change(task_local, task_remote))
            # -> current local task
            #                       -> create new copy
            #                           -> changed taskid
            #                           -> changed name
            # -> current remote task overwrites the current local task

        def local_change_only(task_local, task_remote):
            # util.dbgprint("def local_change_only(task_local, task_remote):")
            # util.dbgprint((local_change(task_local) and not remote_change(task_local, task_remote)))
            return (local_change(task_local) and not remote_change(task_local, task_remote))
            # -> do nothing (will be exported to remote on next export)

        def remote_change_only(task_local, task_remote):
            # util.dbgprint("def remote_change_only(task_local, task_remote):")
            # util.dbgprint((remote_change(task_local, task_remote) and not local_change(task_local)))
            return (remote_change(task_local, task_remote) and not local_change(task_local))
            # -> import (overwrite local)

        def locally_trashed(task_remote):
            # util.dbgprint("def locally_trashed(task_remote):")
            # -> create temp copy
            #                       -> change taskid
            #                       -> change name
            #                       -> save into local trash
            # util.dbgprint (task_remote.taskid in use_task_store_trash.store_dict_id)
            return task_remote.taskid in use_task_store_trash.store_dict_id

        def remotely_trashed(task_local):
            # util.dbgprint("def remotely_trashed(task_local):")
            in_local_not_remote = task_local.taskid not in use_task_remote_store.store_dict_id
            in_remote_known_then_trashed = task_local.export_lamport_timestamp == use_task_store.export_lamport_clock
            # util.dbgprint((in_local_not_remote and in_remote_known_then_trashed))
            return (in_local_not_remote and in_remote_known_then_trashed)
            # -> trash the local copy

        def new_in_local(task_local):
            # util.dbgprint("def new_in_local(task_local):")
            in_local_not_remote = task_local.taskid not in use_task_remote_store.store_dict_id
            in_remote_known_then_trashed = task_local.export_lamport_timestamp == use_task_store.export_lamport_clock
            # util.dbgprint((in_local_not_remote and not in_remote_known_then_trashed))
            return (in_local_not_remote and not in_remote_known_then_trashed)
            # -> do nothing (will be exported to remote on next export)

        def new_in_remote(task_remote):
            # util.dbgprint("def new_in_remote(task_remote):")
            # util.dbgprint((task_remote.taskid not in use_task_store_trash.store_dict_id) and (task_remote.taskid not in use_task_store.store_dict_id))
            return ((task_remote.taskid not in use_task_store_trash.store_dict_id) and (
                task_remote.taskid not in use_task_store.store_dict_id))
            # -> import

        # util.dbgprint("set_tasks_local")
        set_tasks_local = set(use_task_store.store_dict_id.keys())
        # util.dbgprint(str(repr(set_tasks_local)))
        set_tasks_local_processed = set()
        # util.dbgprint("set_tasks_remote")
        set_tasks_remote = set(use_task_remote_store.store_dict_id.keys())
        # util.dbgprint(str(repr(set_tasks_remote)))
        set_tasks_remote_processed = set()

        # go through remote tasks, sync them, mark both sides as processed
        for taskid in set_tasks_remote:
            task_remote = use_task_remote_store.store_dict_id[taskid]
            # util.dbgprint("task_remote.taskid=" + task_remote.taskid + ", name=" + task_remote.name)
            if taskid in set_tasks_local:
                task_local = use_task_store.store_dict_id[taskid]
                # util.dbgprint("task_local.taskid=" + task_local.taskid + ", name=" + task_local.name)
                if remote_change_only(task_local, task_remote):
                    use_task_store.add_deserialized(task_remote)  # import (overwrite local)
                if local_change_only(task_local, task_remote):
                    pass
                if both_change(task_local, task_remote):
                    # -> current local task
                    #                       -> create new copy
                    #                           -> changed taskid
                    #                           -> changed name
                    # -> current remote task overwrites the current local task
                    tmp_task = copy.copy(task_local)
                    tmp_task.name += " (conflicted local copy, conflict date " + util.current_timestamp() + ", orig ID " + tmp_task.taskid + ")"
                    tmp_task.taskid = util.create_id_task()
                    use_task_store.add(tmp_task)
                    use_task_store.add_deserialized(task_remote)
                set_tasks_local_processed.add(task_local.taskid)
                set_tasks_remote_processed.add(task_remote.taskid)

        # go through unprocessed remote tasks, sync them, mark as processed
        for taskid in set_tasks_remote:
            if taskid not in set_tasks_remote_processed:
                task_remote = use_task_remote_store.store_dict_id[taskid]
                # util.dbgprint("task_remote.taskid=" + task_remote.taskid + ", name=" + task_remote.name)
                if locally_trashed(task_remote):
                    # -> create temp copy
                    #                       -> change taskid
                    #                       -> change name
                    #                       -> save into local trash
                    tmp_task = copy.copy(task_remote)
                    tmp_task.name += " (remote backup of locally trashed mote, backup date " + util.current_timestamp() + ", orig ID " + tmp_task.taskid + ")"
                    tmp_task.taskid = util.create_id_task()
                    use_task_store_trash.add(tmp_task)

                if new_in_remote(task_remote):
                    # -> import
                    use_task_store.add_deserialized(task_remote)  # import
            set_tasks_remote_processed.add(task_remote.taskid)

        # go through unprocessed local tasks, sync them, mark as processed
        for taskid in set_tasks_local:
            if taskid not in set_tasks_local_processed:
                task_local = use_task_store.store_dict_id[taskid]
                # util.dbgprint("task_local.taskid=" + task_local.taskid + ", name=" + task_local.name)
                if remotely_trashed(task_local):
                    # -> trash the local copy
                    use_task_store_trash.add_deserialized(task_local)
                    use_task_store.remove(task_local.taskid)
                    pass
                if new_in_local(task_local):
                    # -> do nothing (will be exported to remote on next export)
                    pass
            set_tasks_local_processed.add(task_local.taskid)

        util.tasks_backup(self.task_store, self.task_store_trash, s="imp1")
        return None

    def export_notes(self):
        """
        Exports the task store to a file in the configured path.

        Returns:
            None:
        """

        util.tasks_backup(self.task_store, self.task_store_trash)

        # set clock
        self.task_store.export_lamport_clock = self.task_store.lamport_clock
        for taskid, task in self.task_store.store_dict_id.items():
            task.export_lamport_timestamp = self.task_store.export_lamport_clock

        # save the main database
        self.task_store.task_store_save()
        self.task_store_trash.task_store_save()

        # export to .dat file (without ZIP, so to the same path as the main database)
        self.task_store.task_store_save(alt_path=os.path.join(config.PATH_SAVE_DB, config.FILE_WOOLNOTE_DAT))

        # export the .dat to .zip
        with zipfile.ZipFile(os.path.join(config.PATH_SAVE_DROPBOX_EXPORT, config.FILE_WOOLNOTE_ZIP), "w",
                             compression=zipfile.ZIP_DEFLATED) as exportzip:
            exportzip.write(os.path.join(config.PATH_SAVE_DB, config.FILE_WOOLNOTE_DAT), arcname=config.FILE_WOOLNOTE_DAT,
                            compress_type=zipfile.ZIP_DEFLATED)

    def delete_taskid(self, task_id_list):
        """
        Moves a specified tasks from task store into task trash store.

        Args:
            task_id_list (List[str]): Task ids to be deleted.

        Returns:
            None:
        """
        for taskid in task_id_list:
            task = self.task_store.store_dict_id[taskid]
            self.task_store_trash.add(task)
            self.task_store.remove(taskid)
        self.task_store.task_store_save()
        self.task_store_trash.task_store_save()

    def notes_tagdel(self, task_id_list, tagdel):
        """
        Deletes the specified tag from the tasks from the task store specified by task ids.

        Args:
            task_id_list (List[str]): Task ids to be modified.
            tagdel (str): Tag to be deleted from the specified tasks.

        Returns:
            None:
        """

        for taskid in task_id_list:
            task = self.task_store.store_dict_id[taskid]
            if tagdel in task.tags:
                self.task_store.touch(task.taskid)
                task.tags.discard(tagdel)
        self.task_store.task_store_save()

    def notes_tagadd(self, task_id_list, tagadd):
        """
        Adds the specified tag to the tasks from the task store specified by task ids.

        Args:
            task_id_list (List[str]): Task ids to be modified.
            tagadd (str): Tag to be added to the specified tasks.

        Returns:
            None:
        """
        for taskid in task_id_list:
            task = self.task_store.store_dict_id[taskid]
            self.task_store.touch(task.taskid)
            task.tags.add(tagadd)
        self.task_store.task_store_save()

    def notes_foldermove(self, task_id_list, foldermove):
        """
        Moves the tasks from the task store specified by task ids to the specified folder.
        Args:
            task_id_list (List[str]): Task ids to be moved.
            foldermove (str): Folder which to move tasks to.

        Returns:
            None:
        """
        for taskid in task_id_list:
            task = self.task_store.store_dict_id[taskid]
            self.task_store.touch(task.taskid)
            task.folder = foldermove
        self.task_store.task_store_save()

    def search_notes(self, task_store_name, search_query):
        """
        Returns a list of tasks from the specified task store that match the search query and a list of strings to highlight (matches).
        Args:
            task_store_name (str): Name of the task store where to search. Only certain values are allowed and unknown values fall back to the default task store. (Read the source code for more info.)
            search_query (str): Search query in the language of util.search_expression_tokenizer().

        Returns:
            Tuple[List[str], List[str]]: The list of tasks from the specified task store that match the search query and a list of strings to highlight (matches).
        """
        if task_store_name == "task_store":
            used_task_store = self.task_store
        elif task_store_name == "task_store_trash":
            used_task_store = self.task_store_trash
        elif task_store_name == None:
            used_task_store = self.task_store
        else:
            raise ValueError("Unknown task store name - {}".format(task_store_name))

        tokens = util.search_expression_tokenizer(search_query)
        tree_root = util.search_expression_build_ast(tokens)
        highlight_list = []
        list_taskid_desc = util.search_expression_execute_ast_node(tree_root, used_task_store,
                                                                   fulltext_search_strings=highlight_list)

        return list_taskid_desc, highlight_list
