# University of Illinois/NCSA Open Source License
# Copyright (c) 2017, Jakub Svoboda.

# TODO: docstring for the file
import re
import os
from woolnote import util
from woolnote import config

MARKUP = "MARKUP"
PLAIN = "PLAIN"
# TODO: escape body of notes - prepend a space before every line, ignore unspaced lines

# Task - a single task container
################################

class Task():
    # TODO: add more fields

    def __init__(self):
        """
        Creates a new empty task with default properties.
        """
        super().__init__()
        curr_date = util.current_timestamp()
        self.name = ""
        self.folder = ""
        self.tags = set()
        self.body = ""
        self.taskid = util.create_id_task()
        self.bodydelimiter = util.create_id_task()
        self.lamport_timestamp = 1
        self.export_lamport_timestamp = -1
        self.created_date = curr_date
        self.changed_date = curr_date
        self.due_date = ""
        self.due_date_reminder_dismissed = False
        self.body_format = MARKUP
        self.public_share_auth = util.create_id_task()

    def serialize(self):
        """
        Creates a textual representation of the task so that it can be saved and loaded later.

        Returns:
            str: Serialized task.
        """
        s = util.sanitize_singleline_string_for_tasksave
        if self.folder == "":
            self.folder = config.DEFAULT_FOLDER
        if self.name == "":
            self.name = config.DEFAULT_TASKNAME
        output = []
        output.append("")
        output.append("TASK-BEGIN")
        output.append("TASK-ID " + s(self.taskid))
        output.append("TASK-NAME " + s(self.name))
        output.append("TASK-FOLDER " + s(self.folder))
        output.append("TASK-LAMPORT-TIMESTAMP " + s(str(self.lamport_timestamp)))
        output.append("TASK-EXPORT-LAMPORT-TIMESTAMP " + s(str(self.export_lamport_timestamp)))
        output.append("TASK-CREATED-DATE " + s(self.created_date))
        output.append("TASK-CHANGED-DATE " + s(self.changed_date))
        output.append("TASK-DUE-DATE " + s(self.due_date))
        output.append("TASK-DUE-DATE-REMINDER-DISMISSED " + s(str(self.due_date_reminder_dismissed)))
        output.append("TASK-BODY-FORMAT " + s(self.body_format))
        output.append("TASK-PUBLIC-SHARE-AUTH " + s(self.public_share_auth))
        output.append("TASK-TAGS " + s(", ".join(sorted(self.tags))))
        output.append("TASK-BODY-BEGIN " + s(self.bodydelimiter))
        output.append(self.body)
        output.append("TASK-BODY-END " + s(self.bodydelimiter))
        output.append("TASK-END " + s(self.taskid))
        output.append("")
        output_string = "\n".join(output)
        return output_string

    def deserialize(self, input_string):
        """
        Reads the input_string into self as a transaction. Returns True on success,
        False on fail. Self doesn't change on fail.

        Args:
            input_string (str): The serialized representation of the task

        Returns:
            bool: Whether successful & self changed or unsuccessful & self unchanged.
        """
        tmp_task = Task()
        parse_state_id_known = False
        parse_state_name_known = False
        parse_state_folder_known = False
        parse_state_tags_known = False

        parse_state_lamport_known = False
        parse_state_export_lamport_known = False
        parse_state_created_known = False
        parse_state_changed_known = False
        parse_state_due_known = False
        parse_state_due_rem_known = False
        parse_state_bodyformat_known = False
        parse_state_publicshareauth_known = False

        parse_state_inside_body = False
        parse_state_body_known = False
        parse_state_body = []
        parse_state_body_id_end_delimiter = ""

        # Some conditions may be duplicate for better readability
        for line in input_string.splitlines():
            line = line.rstrip("\n")
            line_split = line.split(" ")
            if not parse_state_inside_body:
                if not parse_state_id_known:
                    if line_split[0] == "TASK-ID":
                        tmp_task.taskid = line_split[1]
                        parse_state_id_known = True
                if not parse_state_name_known:
                    if line_split[0] == "TASK-NAME":
                        tmp_task.name = " ".join(line_split[1:])
                        parse_state_name_known = True
                if not parse_state_folder_known:
                    if line_split[0] == "TASK-FOLDER":
                        tmp_task.folder = " ".join(line_split[1:])
                        parse_state_folder_known = True

                if not parse_state_lamport_known:
                    if line_split[0] == "TASK-LAMPORT-TIMESTAMP":
                        tmp_task.lamport_timestamp = int(line_split[1])
                        parse_state_lamport_known = True
                if not parse_state_export_lamport_known:
                    if line_split[0] == "TASK-EXPORT-LAMPORT-TIMESTAMP":
                        tmp_task.export_lamport_timestamp = int(line_split[1])
                        parse_state_export_lamport_known = True
                if not parse_state_created_known:
                    if line_split[0] == "TASK-CREATED-DATE":
                        tmp_task.created_date = " ".join(line_split[1:])
                        parse_state_created_known = True
                if not parse_state_changed_known:
                    if line_split[0] == "TASK-CHANGED-DATE":
                        tmp_task.changed_date = " ".join(line_split[1:])
                        parse_state_changed_known = True
                if not parse_state_due_rem_known:
                    if line_split[0] == "TASK-DUE-DATE-REMINDER-DISMISSED":
                        tmp_task.due_date_reminder_dismissed = (line_split[1] == "True")
                        parse_state_due_rem_known = True
                if not parse_state_due_known:
                    if line_split[0] == "TASK-DUE-DATE":
                        tmp_task.due_date = " ".join(line_split[1:])
                        parse_state_due_known = True
                if not parse_state_bodyformat_known:
                    if line_split[0] == "TASK-BODY-FORMAT":
                        tmp_task.body_format = line_split[1]
                        parse_state_bodyformat_known = True
                if not parse_state_publicshareauth_known:
                    if line_split[0] == "TASK-PUBLIC-SHARE-AUTH":
                        tmp_task.public_share_auth = line_split[1]
                        parse_state_publicshareauth_known = True

                if not parse_state_tags_known:
                    if line_split[0] == "TASK-TAGS":
                        tags = " ".join(line_split[1:])
                        tags2 = {x.strip() for x in tags.split(",")}
                        tags3 = []
                        for tag in tags2:
                            if tag != "":
                                tags3.append(tag)
                        tmp_task.tags = set(sorted(tags3))
                        parse_state_tags_known = True
                if not parse_state_body_known:
                    if line_split[0] == "TASK-BODY-BEGIN":
                        parse_state_body_id_end_delimiter = line_split[1]
                        tmp_task.bodydelimiter = parse_state_body_id_end_delimiter
                        parse_state_inside_body = True
            elif parse_state_inside_body:
                if line_split[0] == "TASK-BODY-END" and line_split[1] == parse_state_body_id_end_delimiter:
                    parse_state_inside_body = False
                    tmp_task.body = "\n".join(parse_state_body)
                    parse_state_body_known = True
                else:
                    parse_state_body.append(line)

        # start modifying self only after everything is parsed and potential errors or exceptions are the past
        if parse_state_id_known and parse_state_name_known and not parse_state_inside_body and parse_state_body_known:
            self.taskid = tmp_task.taskid
            self.name = tmp_task.name
            self.folder = tmp_task.folder
            self.tags = tmp_task.tags
            self.body = tmp_task.body
            self.bodydelimiter = tmp_task.bodydelimiter

            self.lamport_timestamp = tmp_task.lamport_timestamp
            self.export_lamport_timestamp = tmp_task.export_lamport_timestamp
            self.created_date = tmp_task.created_date
            self.changed_date = tmp_task.changed_date
            self.due_date = tmp_task.due_date
            self.due_date_reminder_dismissed = tmp_task.due_date_reminder_dismissed
            self.body_format = tmp_task.body_format
            self.public_share_auth = tmp_task.public_share_auth

            return True

        return False


# TaskStore - a container for many tasks
########################################

class TaskStore():
    def __init__(self, filepath):
        """
        Creates an in-memory task store that can load or save its contents from/to a file, can accept new tasks, can
        perform searches over tasks.

        Args:
            filepath (str): File into which and from which tasks can be saved / loaded.
        """
        super().__init__()
        self.store_dict_id = {}
        self.lamport_clock = 1
        self.export_lamport_clock = -1  # lamport clock at the last export (not just save, but the user-facing export functionality)
        self.last_import_lamport_clock = -1  # lamport clock at the last import (not just save, but the user-facing export functionality)
        self.filepath = filepath
        self.taskids_touched_since_last_add_or_del = set()
        self.taskids_touched_dict_cleared_since_last_save = False

    def serialize(self):
        """
        Returns a textual representation of itself and all tasks.

        Returns:
            str: serialized task store
        """
        s = util.sanitize_singleline_string_for_tasksave
        serialized_list = []
        serialized_list.append("EXPORT-LAMPORT-CLOCK " + s(str(self.export_lamport_clock)) + "\n")
        serialized_list.append("LAST-IMPORT-LAMPORT-CLOCK " + s(str(self.last_import_lamport_clock)) + "\n")

        # sort by taskid so that unix text diff between two different serialized export is easy
        taskid_list = sorted(self.store_dict_id)
        for taskid in taskid_list:
            task = self.store_dict_id[taskid]
            serialized_list.append(task.serialize())
            serialized_list.append("\n\n")
        serialized = "".join(serialized_list)
        return serialized

    def task_store_save(self, alt_path=None):
        """
        Saves the serialized itself into the file configured in __init__(). This method has to be called manually,
        the task store doesn't save its in-memory representation into the file automatically. If no alternative path
        is specified and if only a few tasks have been modified (without deleting or adding), it saves the changes
        to a small differential file. If no alternative path is specified but the changes are more extensive,
        the full file is saved and the differential file is emptied. If an alternative path is specified, no diff file
        is used.

        Args:
            alt_path (Union[str, None]): Alternative path where to save.

        Returns:
            None:
        """

        path_diff = self.filepath + config.DIFFNEW_EXTENSION
        if all([ alt_path is None,  # only if primary location
                 not self.taskids_touched_dict_cleared_since_last_save,  # only if flush not necessary
                 self.taskids_touched_since_last_add_or_del,  # only if something has been touched
                 len(self.taskids_touched_since_last_add_or_del) in range(5),  # only if only a few has been touched
                 ]) :
            # no alternative path, saving to the primary location
            # there is only a few tasks that have been modified, write them to a separate small file

            diffupdate_store = TaskStore(None)
            for taskid in self.taskids_touched_since_last_add_or_del:
                task = self.store_dict_id[taskid]
                diffupdate_store.add_deserialized(task)
            with open(path_diff, "w", encoding="utf-8") as stored_file:
                stored_file.write(diffupdate_store.serialize())

        elif alt_path is None:
            # no alternative path, saving to the primary location
            # empty the separate small file and save everything to the main file

            self.taskids_touched_since_last_add_or_del.clear()  # going to save the full file
            self.taskids_touched_dict_cleared_since_last_save = False  # going to save the full file and begin with a clean slate again
            with open(self.filepath, "w", encoding="utf-8") as stored_file:
                stored_file.write(self.serialize())
            with open(path_diff, "w", encoding="utf-8") as stored_file:
                stored_file.write("")

        else:
            # alternative path, do not use differential files at all

            with open(alt_path, "w", encoding="utf-8") as stored_file:
                stored_file.write(self.serialize())

    def task_store_load(self, alt_path=None):
        """
        Loads the serialized data from the file configured in __init__(), deserializes them and adds them to any data
         that were held in memory by the task store.

        Args:
            alt_path (Union[str, None]): Alternative path where to load from.

        Returns:
            None:
        """

        def deserialize(destination_task_store, source_file, list_of_taskids_read=None):
            """
            Deserialize task store data from an input file and save it to a TaskStore instance.

            Args:
                destination_task_store (woolnote.task_store.TaskStore): where to store the deserialized data
                source_file (_io.TextIOWrapper): where to read serialized data from
                list_of_taskids_read (Union[None, List]): if not None, append deserialized taskid to this list

            Returns:
                None:
            """
            task_strings = []
            inside_task = False
            inside_task_id_known = False
            inside_task_id = ""
            for line in stored_file:
                line = line.rstrip("\n")
                line_split = line.split(" ")
                if not inside_task:
                    if line_split[0] == "EXPORT-LAMPORT-CLOCK":
                        destination_task_store.export_lamport_clock = int(line_split[1])
                    if line_split[0] == "LAST-IMPORT-LAMPORT-CLOCK":
                        destination_task_store.last_import_lamport_clock = int(line_split[1])
                    if line == "TASK-BEGIN":
                        inside_task = True
                if inside_task:
                    task_strings.append(line)
                    if not inside_task_id_known:
                        if line_split[0] == "TASK-ID":
                            inside_task_id = line_split[1]
                            inside_task_id_known = True
                    if inside_task_id_known:
                        if line_split[0] == "TASK-END":
                            if line_split[1] == inside_task_id:
                                inside_task = False
                                inside_task_id_known = False
                                new_task = Task()
                                new_task.deserialize("\n".join(task_strings))
                                destination_task_store.add_deserialized(new_task)
                                if list_of_taskids_read is not None:
                                    list_of_taskids_read.append(new_task.taskid)
                                task_strings = []

        self.taskids_touched_since_last_add_or_del.clear()  # loading different data, the old are going to be irrelevant
        self.taskids_touched_dict_cleared_since_last_save = True  # this makes task_store_save() work properly - deletes the contents of the diff file

        path = self.filepath
        if alt_path is not None:
            path = alt_path
        with open(path, "r", encoding="utf-8") as stored_file:
            deserialize(self, stored_file)

        # TODO test this functionality!
        path_diff = self.filepath + config.DIFFNEW_EXTENSION
        if alt_path is None and os.path.isfile(path_diff):
            # load is not from alternative path -> load differential file if it exists
            with open(path_diff, "r", encoding="utf-8") as stored_file:
                list_of_diff_taskids = []
                deserialize(self, stored_file, list_of_diff_taskids)
                self.taskids_touched_since_last_add_or_del.update(list_of_diff_taskids)
                self.taskids_touched_dict_cleared_since_last_save = False  # loaded the previous state with some tasks in the diff file and this state can be further used


    def add_deserialized(self, task):
        """
        Adds a new task and doesn't advance the lamport clock.

        Args:
            task (woolnote.task_store.Task): Task to add.

        Returns:
            None:
        """
        self.store_dict_id[task.taskid] = task
        self.lamport_clock = max(self.lamport_clock, int(task.lamport_timestamp))
        self.taskids_touched_since_last_add_or_del.clear()

    def update_lamport_clock(self, ext_clock):
        """
        Updates internal lamport clock according to external clock.

        Args:
            ext_clock (int): External lamport clock

        Returns:
            None:
        """
        self.lamport_clock = max(self.lamport_clock, int(ext_clock))

    def add(self, task):
        """
        Adds a new task and advances the lamport clock both in the added task and in the task store.

        Args:
            task (woolnote.task_store.Task):

        Returns:
            None:
        """
        self.store_dict_id[task.taskid] = task
        self.lamport_clock = 1 + max(self.lamport_clock, int(task.lamport_timestamp))
        task.lamport_timestamp = self.lamport_clock
        self.taskids_touched_since_last_add_or_del.clear()
        self.taskids_touched_dict_cleared_since_last_save = True

    def touch(self, taskid):
        """
        Advances the lamport clock both on the task by the given taskid and on the task store itself. The task store's
        internal lamport clock is used as the reference.

        Args:
            taskid (str): identifies the task for which to advance the lamport clock

        Returns:
            None:
        """
        self.lamport_clock = 1 + max(self.lamport_clock, int(self.store_dict_id[taskid].lamport_timestamp))
        self.store_dict_id[taskid].lamport_timestamp = self.lamport_clock
        self.taskids_touched_since_last_add_or_del.add(taskid)

    def sort_taskid_list_descending_lamport_helper(self, taskid_list):
        """
        Sorts the input list of taskids by lamport clock in descending order. No state is changed.

        Args:
            taskid_list (Union[dict_keys, List[str]]): A list of taskids identifying which tasks to sort.

        Returns:
            List[str]: taskids sorted by lamport clock in descending order
        """
        tuples_taskid_lamport = []
        for taskid in taskid_list:
            task = self.store_dict_id[taskid]
            lamport = task.lamport_timestamp
            tuples_taskid_lamport.append((taskid, lamport))
        sorted_tuples = sorted(tuples_taskid_lamport, key=lambda x: x[1], reverse=True)
        sorted_taskid_desc = [x[0] for x in sorted_tuples]
        return sorted_taskid_desc

    def sort_taskid_list_descending_lamport(self):
        """
        Returns a list of taskids (of all tasks in the task store) sorted by their lamport clock in descending order.
        No state is changed.

        Returns:
            List[str]: taskids sorted by lamport clock in descending order
        """
        sorted_taskid_desc = self.sort_taskid_list_descending_lamport_helper(self.store_dict_id.keys())
        return sorted_taskid_desc

    def remove(self, taskid):
        """
        Removes the reference to the task of the given taskid from the task store. Doesn't advance the removed task's
        lamport clock but it does advance the task store's lamport clock by 1.

        Args:
            taskid (str): Taskid identifying the task to be deleted from the task store.

        Returns:
            None:
        """
        self.lamport_clock += 1
        del (self.store_dict_id[taskid])
        self.taskids_touched_since_last_add_or_del.clear()
        self.taskids_touched_dict_cleared_since_last_save = True

    def get_folder_list(self):
        """
        Returns a list of folders. The list is obtained by iterating through all tasks in the task store and reading the
        names of the folders they have set. Each task can belong to exactly one folder and the folder is a string.

        Returns:
            List[str]: List of all folders used by all the tasks.
        """
        folder_set = set()
        for taskid, task in self.store_dict_id.items():
            if task.folder:
                folder_set.add(task.folder)
        folder_list = sorted(folder_set)
        return folder_list

    def get_tag_list(self):
        """
        Returns a list of tags. The list is obtained by iterating through all tasks in the task store and reading the
        names of the tags they have set. Each task can have zero or more tags set and each tag is a string.

        Returns:
            List[str]: List of all tags used by all the tasks.
        """
        tag_set = set()
        for taskid, task in self.store_dict_id.items():
            for tag in task.tags:
                if tag:
                    tag_set.add(tag)
        tag_list = sorted(tag_set)
        return tag_list

    def get_context_list(self):
        """
        Returns the list of GTD context strings from the bodies of all tasks. A GTD context string is in the form of
        "@someword". This method returns only those such strings that don't immediately follow with a dot and more
        characters (that would be an email address) and that don't have characters immediately before the @ sign
        (that would again be an email address).

        Returns:
            List[str]:
        """
        context_set = set()
        ctx_re = re.compile("""(?<!\w)       # Negative lookbehind, not included in matched string
                                             #  - character immediately preceding @ - that would be
                                             #  an email address and we don't want to match that.
                               (             # The matched GTD context string.
                                @            # Every GTD context starts with @ and we want to
                                             #  leave the @ symbol in the matched strings.
                                (?!\w+\.\w+) # Negative lookahead, not included in matched string -
                                             #  the string immediately following @ must not consist
                                             #  of letter(s), dot, and letter(s) - that would be an
                                             #  email address and we don't want to match that.
                                \w+          # One or more characters in the GTD context string.
                               )             # End of the matched string.
                            """, re.VERBOSE)
        for taskid, task in self.store_dict_id.items():
            contexts = ctx_re.findall(task.body)
            contexts = [x.lower() for x in contexts]
            context_set = context_set.union(contexts)
        context_list = sorted(context_set)
        return context_list

    def filter_folder(self, folder):
        """
        Returns only those taskids from the task store which are in the specified folder.

        Args:
            folder (str): folder

        Returns:
            List[str]: taskids from the given folder
        """
        list_taskid_unfiltered = self.sort_taskid_list_descending_lamport()
        list_taskid_filtered = []
        for taskid in list_taskid_unfiltered:
            task = self.store_dict_id[taskid]
            if task.folder.lower() == folder.lower():
                list_taskid_filtered.append(task.taskid)
        return list_taskid_filtered

    def filter_tag(self, tag):
        """
        Returns only those taskids from the task store which have the specified tag.

        Args:
            tag (str): tag

        Returns:
            List[str]: taskids for the given tag
        """
        list_taskid_unfiltered = self.sort_taskid_list_descending_lamport()
        list_taskid_filtered = []
        for taskid in list_taskid_unfiltered:
            task = self.store_dict_id[taskid]
            if tag.lower() in [tasktag.lower() for tasktag in task.tags]:
                list_taskid_filtered.append(task.taskid)
        return list_taskid_filtered

    def filter_search(self, search_text):
        """
        Returns only those taskids from the task store which contain the specified text. Search is case-insensitive.

        Args:
            search_text (str): case-insensitive text to be searched

        Returns:
            List[str]: taskids matching the searched text.
        """
        list_taskid_unfiltered = self.sort_taskid_list_descending_lamport()
        list_taskid_filtered = []
        for taskid in list_taskid_unfiltered:
            task = self.store_dict_id[taskid]
            name_found = search_text.lower() in task.name.lower()
            body_found = search_text.lower() in task.body.lower()
            taskid_found = search_text.lower() in task.taskid.lower()
            due_found = search_text.lower() in task.due_date.lower()
            created_found = search_text.lower() in task.created_date.lower()
            changed_found = search_text.lower() in task.changed_date.lower()
            if name_found or body_found or taskid_found or due_found or created_found or changed_found:
                list_taskid_filtered.append(task.taskid)
        return list_taskid_filtered
