# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

# TODO: docstring for the file
# woolnote config class
#######################
from woolnote.task_store import Task
from woolnote import tests


class WoolnoteConfig:
    """
        Runtime configuration for woolnote. Contains user prefs. Doesn't contain import/export/save paths (these are outside of configuration, hardcoded at the beginning of the .py file).
        Uses a note from the provided task_store (TaskStore instance) with the name in CONFIG_TASK_NAME for retrieving the configuration.
        Use read_from_config_note(task_store) to load the active configuration.
        Other code can directly read properties of the WoolnoteConfig instance to get the current config.
    """
    CONFIG_TASK_NAME = "_woolnote_config"
    CONFIG_VIRTFLDR_PARAM_NAME = "virtualfolder"
    CONFIG_TASK_DEFAULT_BODY = """
**woolnote configuration**

Unrecognized lines are ignored.

**Virtual Folders**
Virtual folders are saved search expressions that are evaluated at the time of opening the virtual folder.
Setting one virtual folder is done by putting one line of the form "^virtualfolder===={0}===={1}" in the """ + CONFIG_TASK_NAME + """ note, where "^" is the beginning of line (meaning there can be no preceding characters and the line begins with virtualfolder), {0} is the name of the virtual folder and {1} is the search expression which must not contain newline characters.

Here is an example of a virtual folder:

virtualfolder====Virtual Folder Example====((fulltext: ("SOME")) and ((tag: "SEARCH") or (folder: "EXPRESSION"))) and 'AS AN EXAMPLE OF "VIRTUAL FOLDERS"'

**Quick Single Line Notes**
It is possible to directly enter one-line notes from the main screen through a ***single line note ID***. This is useful when you often enter new one-line notes into specific notes. To create a new ***single line note ID***, enter the text ***#^#:my chosen name:#^#*** where "my chosen name" can be anything, e.g. "supermarket shopping list". The lines entered through this functionality are inserted directly above the ***#^#:...:#^#*** line. If a specific ***single line note ID*** is present more than one time in all notes in total, it is ***removed*** from the list of detected IDs and can't be used; to make it usable, you need to first eliminate all occurrences but the one to be used.

**Help - Search Expressions**
Search expression control sequences are case sensitive (always lower case) and the search expression search strings are case insensitive (always converted to lower case and the matched text always converted to lower case).
Search expression search strings are the strings that are searched in the notes.
Search expression control sequences are: **fulltext:** **tag:** **folder:** **(** **)** **"** **'** **and** **or** **not**.
* **"** encloses only a search string that doesn't contain the **"** character.
* **'** encloses only a search string that doesn't contain the **'** character.
* **(** and **)** enclose a search string if the enclosed string doesn't begin with a control sequence or it encloses a search expression if it begins with a control sequence.
** **(milk and cheese)** is evaluated as a search string.
** **((milk) and (cheese))** is evaluated as a search for **(milk)** combined using **and** with a search for **(cheese)** and **(milk)** is evaluated as a fulltext search for **milk** and **(cheese)** is evaluated in the same way.
* **fulltext:** sets the enclosed following searches to the ***fulltext*** search mode, unless some enclosed search is preceded with a different search type.
** The fulltext search mode searches in the note name, body, folder, tags, task id, due date, changed date, created date.
* **tag:** sets the enclosed following searches to the ***tag*** search mode, unless some enclosed search is preceded with a different search type.
** The tag search mode searches in the names of the tags the note has.
* **folder:** sets the enclosed following searches to the ***folder*** search mode, unless some enclosed search is preceded with a different search type.
** The folder search mode searches in the name of the folder the note is in.
* **and** and **or** can glue together two or more subexpressions and perform the logical operations ***and*** and ***or***. At one level of expressions, only **and** or only **or** can be used; to use both, you need to nest subexpressions into **(** **)**.
** ***and*** returns only those tasks which are present in both subexpressions.
** ***or*** returns those tasks which are present either of the subexpression.
* **not** can precede an expression and negates its selection. E.g. if there are notes "1", "2", "3", "4", then the expression "not 3" will result in "1", "2", "4". The **not** operator cannot appear at the same level of expression as **and** or **or**; you need to nest subexpressions into **(** **)**.
** To connect three subexpressions using more than one operator (**and**/**or**/**not**), use **(** **)** to enclose them into pairs or into tuples that use the same operator within a single tuple: **((first expression) and (second expression)) or (third expression)**
** This is invalid because it connects subexpressions using dissimilar operators: **(first expression) and (second expression) or (third expression)**
** This is valid because it connects subexpressions using only one type of operator: **(first expression) and (second expression) and (third expression)**
Examples:
**text not beginning with a control sequence** - fulltext search for the whole text
**((lentils) or beans or bananas)** - equivalent of **("lentils" or "beans or bananas")**
**("lentils" or "beans" or "bananas") and (not "motor oil")**
**(tag: ((tag 1) or (tag2))) or (tag3)** - equivalent of **((tag:"tag 1") or (tag:"tag2")) or (tag:"tag3")** - equivalent of **((tag:tag 1) or tag:tag2) or (tag: tag3)** - equivalent of **( ( tag:tag 1)  or  tag:tag2) or  tag: tag3** - equivalent of **tag:"tag 1"  or  tag:(tag2) or  tag: 'tag3'**

**Help - Formatting**
__underline__
---strikethrough---
**bold**
***italics***
****bold italics****
arbitrary [ ] checkbox or checked [x] checkbox
* bullet list
* bullet list
- checkbox list
- checkbox list
** bullet list 2nd level
** bullet list 2nd level
*** bullet list 3rd level
*** bullet list 3rd level
** 2nd level bullet list __with__ **formatting** and [ ] a checkbox

horizontal line:
___




"""

    def __init__(self):
        # TODO: docstring
        super().__init__()

        # dict[name, search string]
        self.virtual_folders = {}

        # dict[id, taskid]
        self.single_note_line_id = {}

    @tests.integration_method("web_ui")
    def save_default_config_note(self, task_store):
        # TODO: docstring
        """

        Returns:

        """
        task = Task()
        task.name = self.CONFIG_TASK_NAME
        task.body = self.CONFIG_TASK_DEFAULT_BODY
        task_store.add(task)

    @tests.integration_method("web_ui")
    def read_from_config_note(self, task_store):
        """
        Reads configuration from notes.
        Reads virtualfolder configuration from the config note and single note line IDs from all the notes.
        The read data are saved into `self.virtual_folders` and `self.single_note_line_id`.

        Args:
            task_store (woolnote.task_store.TaskStore):

        Returns:
            None:
        """
        self.virtual_folders = {}
        contents = None
        list_taskid_unfiltered = task_store.sort_taskid_list_descending_lamport()
        for taskid in list_taskid_unfiltered:
            task = task_store.store_dict_id[taskid]
            if task.name == self.CONFIG_TASK_NAME:
                contents = task.body
        if contents is None:
            self.save_default_config_note(task_store)
            contents = self.CONFIG_TASK_DEFAULT_BODY
        if contents is not None:
            for line in contents.split("\n"):
                if line.startswith(self.CONFIG_VIRTFLDR_PARAM_NAME + "===="):
                    # expecting strings like: virtualfolder====name====search term
                    try:
                        paramtype, paramname, paramcontent = line.split("====", 2)
                        if paramtype == self.CONFIG_VIRTFLDR_PARAM_NAME:
                            self.virtual_folders[paramname] = paramcontent
                    except:
                        pass

        self.single_note_line_id = {}
        # those present more than once
        self.single_note_line_id_invalid = set()
        list_taskid_unfiltered = task_store.filter_search("#^#:")
        for taskid in list_taskid_unfiltered:
            task = task_store.store_dict_id[taskid]
            contents = task.body
            if contents is not None:
                for line in contents.split("\n"):
                    if line.endswith(":#^#") and any((line.startswith("#^#:"), line.startswith("- #^#:"),
                                                      line.startswith("+ #^#:"), line.startswith("* #^#:"),
                                                      line.startswith("** #^#:"), line.startswith("*** #^#:"),
                                                      line.startswith("**** #^#:") )):
                        id = line.split("#^#:")[1].split(":#^#")[0]
                        if id in self.single_note_line_id_invalid:
                            continue
                        if id in self.single_note_line_id:
                            self.single_note_line_id_invalid.add(id)
                            del self.single_note_line_id[id]
                            continue
                        else:
                            self.single_note_line_id[id] = taskid
