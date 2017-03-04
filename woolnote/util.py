# University of Illinois/NCSA Open Source License
# Copyright (c) 2017, Jakub Svoboda.

# TODO: docstring for the file
import random
import html
import time
import os
import hashlib
import urllib

from woolnote import config

# debug output can be toggled with debug_print for the whole file
debug_print = True


# Use dbgprint() instead of print() for debug output so that it can be toggled.
def dbgprint(arg):
    """Debug print helper function - debug output can be toggled with debug_print for the whole file."""
    if debug_print:
        print(arg)


# search expression language parsing
####################################

class Search_AST_Node:
    """Used for building an AST for search expressions"""

    def __init__(self):
        # TODO: docstring
        super().__init__()
        self.children = []
        self.parent = None
        self.type = None
        self.content = None

    def toString(self):
        # TODO: docstring
        out = ["type {} contents {}".format(self.type, self.content)]
        for child in self.children:
            childout = child.toString().split("\n")
            for line in childout:
                out.append(" " + line)
        return "\n".join(out)


def search_expression_tokenizer(filter_expression):
    # TODO: docstring
    dbgprint("dbg search_expression_tokenizer start")
    dbgprint("filter string: " + repr(filter_expression) + " " + str(type(filter_expression)))
    # valid queries:
    # single fulltext search string that (contains) "special" characters but not at the beginning
    # ("query that uses a special character at the beginning - the first special char encloses the query)
    # "(query that uses a special character at the beginning - the first special char encloses the query"
    # '"query that uses a special character at the beginning - the first special char encloses the query'
    # fulltext: A fulltext query even if it begins with "folder: " or "tag: "
    # folder: Filter by folder
    # tag: Filter by tag
    # (one query) and (another query)
    # "one query" and (another query)
    # ((one query) and (another query)) or (third query)
    #
    # invalid queries:
    # composed queries cannot be inside quotes - they are interpreted as strings
    # -> this is invalid: "(one query) and (another query)" and (third query)
    # this is interpreted as one string:
    # some string or another string
    #
    # resulting types of tokens:
    # SEARCH_STRING
    # CTRL_SEQ_CLOSING
    # CTRL_SEQ_OPERATOR
    # CTRL_SEQ_OPENING
    # CTRL_SEQ_SEARCH_TYPE

    STRING_CTRL_SEQ_BEGINNING = ["(", '"', "'", "fulltext:", "folder:", "tag:"]
    STRING_CTRL_OPERATOR = ["and", "or"]
    SINGLE_CHAR_WHITESPACE = [" ", "\t"]

    rest_of_filter_expression = filter_expression
    tokens = []
    loop_run = True
    inside_search_string = False
    # TODO: strip trailing spaces from search string if not inside quotes
    search_string_so_far = ""
    waiting_for_ctrl_char = []

    def last_waiting_for_ctrl_char():
        try:
            return waiting_for_ctrl_char[-1]
        except:
            None

    def commit_search_string_to_tokens():
        nonlocal inside_search_string
        nonlocal search_string_so_far
        nonlocal tokens  # not necessary, just for clarity

        if inside_search_string:
            inside_search_string = False
            if search_string_so_far:
                tokens.append(("SEARCH_STRING", search_string_so_far))
                search_string_so_far = ""

    while loop_run:
        curr_char_is_whitespace = False
        curr_char_is_awaited_closing_ctrl_char = False
        curr_beg_is_control = False
        curr_beg_is_operator = False
        token_string = ""
        loop_skip_to_next = False

        # do not continue if there's nothing left to parse
        # the only unparsed thing may be the search string and so it is additionally parsed after the loop
        if not rest_of_filter_expression:
            loop_run = False
            break

        # detect closing control char
        if last_waiting_for_ctrl_char():
            if rest_of_filter_expression[0] == last_waiting_for_ctrl_char():
                curr_char_is_awaited_closing_ctrl_char = True
                commit_search_string_to_tokens()
                token_string = waiting_for_ctrl_char.pop()
                tokens.append(("CTRL_SEQ_CLOSING", token_string))
                rest_of_filter_expression = rest_of_filter_expression[len(token_string):]
                continue

        # detect whitespace
        if not inside_search_string:
            curr_char_is_whitespace = rest_of_filter_expression[0] in SINGLE_CHAR_WHITESPACE
            if curr_char_is_whitespace:
                rest_of_filter_expression = rest_of_filter_expression[1:]
                continue

        # detect and/or
        if not inside_search_string:
            for ctrlseq in STRING_CTRL_OPERATOR:
                if rest_of_filter_expression.startswith(ctrlseq):
                    curr_beg_is_operator = True
                    token_string = ctrlseq
                    tokens.append(("CTRL_SEQ_OPERATOR", token_string))
                    rest_of_filter_expression = rest_of_filter_expression[len(token_string):]
                    loop_skip_to_next = True
                    break  # break out of the inner for loop

        if loop_skip_to_next:
            continue

        # detect opening control char
        if not inside_search_string:
            for ctrlseq in STRING_CTRL_SEQ_BEGINNING:
                if rest_of_filter_expression.startswith(ctrlseq):
                    curr_beg_is_control = True
                    token_string = ctrlseq
                    if ctrlseq == "(":
                        waiting_for_ctrl_char.append(")")
                        tokens.append(("CTRL_SEQ_OPENING", token_string))
                    elif (ctrlseq == "'") or (ctrlseq == '"'):
                        inside_search_string = True
                        waiting_for_ctrl_char.append(ctrlseq)
                        tokens.append(("CTRL_SEQ_OPENING", token_string))
                    else:
                        tokens.append(("CTRL_SEQ_SEARCH_TYPE", token_string))
                    rest_of_filter_expression = rest_of_filter_expression[len(token_string):]
                    loop_skip_to_next = True
                    break  # break out of the inner for loop

        if loop_skip_to_next:
            continue

        # the current character belongs to a search string
        search_string_so_far += rest_of_filter_expression[0]
        rest_of_filter_expression = rest_of_filter_expression[1:]
        inside_search_string = True

    # the expression may have ended with the search string and it may need to be commited
    commit_search_string_to_tokens()

    dbgprint("tokens: " + repr(tokens))
    return tokens


def search_expression_build_ast(tokens):
    # TODO: docstring
    # recognized types of tokens:
    # SEARCH_STRING - sets the current token type and content
    # CTRL_SEQ_CLOSING - moves the current position pointer up by parents to the first matching opening token
    # CTRL_SEQ_OPERATOR - creates two children to the current position token, copies type and contents of the current position token to the first child, rewrites the type and contents of the current position token by the new CTRL_SEQ_OPERATOR, moves the current position pointer to the second child; the second child remains empty
    # CTRL_SEQ_OPENING - sets the current token type and content, inserts an empty child and moves the current position pointer there
    # CTRL_SEQ_SEARCH_TYPE - sets the current token type and content, inserts an empty child and moves the current position pointer there
    # new type of token
    # CTRL_SEQ_CLOSED - when the CTRL_SEQ_CLOSING arrives at CTRL_SEQ_OPENING
    # TODO: valid token transitions (which tokens can have which children)


    # set up the execute root and one empty child as the current position
    list_of_nodes = []  # < TODO: delete
    execute_root = Search_AST_Node()
    list_of_nodes.append(execute_root)
    current_position = Search_AST_Node()
    list_of_nodes.append(current_position)
    current_position.parent = execute_root
    execute_root.children.append(current_position)
    execute_root.type = "EXEC_ROOT"
    execute_root.content = None

    # TODO: asserts what can and cannot happen

    for (token_type, token_content) in tokens:
        dbgprint("ast dbg: {} {}".format(token_type, token_content))
        if token_type == "SEARCH_STRING":
            current_position.type = token_type
            current_position.content = token_content
        elif token_type == "CTRL_SEQ_CLOSING":
            dbgprint("ast dbg closing")
            while current_position.type != "CTRL_SEQ_OPENING":
                dbgprint("ast dbg closing while {}".format(current_position.type))
                current_position = current_position.parent
            dbgprint("ast dbg closed after while {}".format(current_position.type))
            current_position.type = "CTRL_SEQ_CLOSED"
        elif token_type == "CTRL_SEQ_OPERATOR":
            parent = current_position.parent

            # the inserted node takes place of the current position node and the current position node becomes the first child of the inserted node

            inserted_node = Search_AST_Node()
            list_of_nodes.append(inserted_node)
            inserted_node.type = token_type
            inserted_node.content = token_content
            inserted_node.parent = parent

            # replace the child of parent - put the inserted node instead of the current position node
            parent.children = [inserted_node if child == current_position else child for child in parent.children]

            first_child = current_position
            first_child.parent = inserted_node
            inserted_node.children.append(first_child)

            second_child = Search_AST_Node()
            list_of_nodes.append(second_child)
            second_child.parent = inserted_node
            inserted_node.children.append(second_child)

            current_position = second_child
        elif token_type == "CTRL_SEQ_OPENING":
            current_position.type = token_type
            current_position.content = token_content
            child = Search_AST_Node()
            list_of_nodes.append(child)
            child.parent = current_position
            current_position.children.append(child)
            current_position = child
        elif token_type == "CTRL_SEQ_SEARCH_TYPE":
            current_position.type = token_type
            current_position.content = token_content
            child = Search_AST_Node()
            list_of_nodes.append(child)
            child.parent = current_position
            current_position.children.append(child)
            current_position = child
        else:
            # TODO: throw exception - unknown token type
            dbgprint("ERROR in search_expression_build_ast!")

    dbgprint(execute_root.toString())

    # basic sanity check
    # we don't care about invalid expressions much (until woolnote strives to be general-user-friendly)
    if execute_root.type != "EXEC_ROOT":
        return None
    if execute_root.content != None:
        return None

    return execute_root


def search_expression_execute_ast_node(ast_node, task_store, search_type=None, fulltext_search_strings=None):
    # TODO: docstring
    # TODO doscstring about fulltext_search_strings changing the return value
    # fulltext_search_strings is None or list. if it is list, then all fulltext search strings will be appended to it
    # works correctly only on EXEC_ROOT for end user
    # recognized types of tokens:
    # EXEC_ROOT
    # SEARCH_STRING
    # CTRL_SEQ_OPERATOR
    # CTRL_SEQ_SEARCH_TYPE
    # CTRL_SEQ_CLOSED
    if ast_node.type == "EXEC_ROOT":
        unsorted_list = search_expression_execute_ast_node(ast_node.children[0], task_store,
                                                           fulltext_search_strings=fulltext_search_strings)
        sorted_list = task_store.sort_taskid_list_descending_lamport_helper(list(set(unsorted_list)))
        return sorted_list
    elif ast_node.type == "SEARCH_STRING":
        if search_type is None:
            if fulltext_search_strings is not None:
                fulltext_search_strings.append(ast_node.content)
            return task_store.filter_search(ast_node.content)
        elif search_type == "fulltext:":
            if fulltext_search_strings is not None:
                fulltext_search_strings.append(ast_node.content)
            return task_store.filter_search(ast_node.content)
        elif search_type == "folder:":
            return task_store.filter_folder(ast_node.content)
        elif search_type == "tag:":
            return task_store.filter_tag(ast_node.content)
        else:
            return None
    elif ast_node.type == "CTRL_SEQ_OPERATOR":
        if ast_node.content == "and":
            list1 = search_expression_execute_ast_node(ast_node.children[0], task_store, search_type=search_type,
                                                       fulltext_search_strings=fulltext_search_strings)
            list2 = search_expression_execute_ast_node(ast_node.children[1], task_store, search_type=search_type,
                                                       fulltext_search_strings=fulltext_search_strings)
            and_list = []
            for item in list1:
                if item in list2:
                    and_list.append(item)
            sorted_and_list = task_store.sort_taskid_list_descending_lamport_helper(list(set(and_list)))
            return sorted_and_list
        elif ast_node.content == "or":
            list1 = search_expression_execute_ast_node(ast_node.children[0], task_store, search_type=search_type,
                                                       fulltext_search_strings=fulltext_search_strings)
            list2 = search_expression_execute_ast_node(ast_node.children[1], task_store, search_type=search_type,
                                                       fulltext_search_strings=fulltext_search_strings)
            or_list = list(set(list1 + list2))
            sorted_or_list = task_store.sort_taskid_list_descending_lamport_helper(or_list)
            return sorted_or_list
    elif ast_node.type == "CTRL_SEQ_SEARCH_TYPE":
        return search_expression_execute_ast_node(ast_node.children[0], task_store, search_type=ast_node.content,
                                                  fulltext_search_strings=fulltext_search_strings)
    elif ast_node.type == "CTRL_SEQ_CLOSED":
        return search_expression_execute_ast_node(ast_node.children[0], task_store, search_type=search_type,
                                                  fulltext_search_strings=fulltext_search_strings)
    else:
        # bad input
        return None


# helper functions for core functionality and web backend & frontend
####################################################################

def current_timestamp():
    # TODO: docstring
    curr_date = str(time.strftime("%Y-%m-%d %H:%M:%S"))
    return curr_date


def create_id_task():
    # TODO: docstring
    """Creates a random ID consisting of 64 [01-9A-F] symbols."""
    return "{:064X}".format(random.randrange(16 ** 64))


def generate_one_time_pwd():
    # TODO: docstring
    """Creates a random password with [01-9A-F] symbols and 8 characters for one-time passwords."""
    return "{:8x}".format(random.randrange(16 ** 8))


def sanitize_singleline_string_for_tasksave(unsafe):
    # TODO: docstring
    # TODO: can this be broken by other unicode newline characters?
    new = unsafe.replace("\n", "")
    new = new.replace("\r", "")
    new = new.strip()
    return new


def sanitize_singleline_string_for_html(unsafe):
    # TODO: docstring
    # http://php.net/htmlspecialchars
    # http://stackoverflow.com/questions/1061697/whats-the-easiest-way-to-escape-html-in-python
    # http://stackoverflow.com/questions/3096948/escape-html-in-python
    # https://wiki.python.org/moin/EscapingHtml
    new = unsafe.replace("\n", "")
    new = new.replace("\r", "")
    safe = html.escape(new)
    return safe


def sanitize_multiline_string_for_textarea_html(unsafe):
    # TODO: docstring
    new = html.escape(unsafe)
    return new


def convert_multiline_plain_string_into_safe_html(unsafe):
    # TODO: docstring
    new = unsafe.replace("\r", "")
    new = html.escape(new)
    new = new.replace("\n", "<br>\n")
    return new


def task_body_save_fix_newlines(plain):
    # TODO: docstring
    return plain.replace("\r", "")

def task_body_save_fix_multiline_markup_bullet_lists(plain):
    # TODO: docstring
    """Replicates last used bullet list/task list style on the immediately following non-empty lines (so that the user has easier input). Prepends and appends at least 4 newlines if there are less than 4 newlines on the beginning/end."""
    lines = plain.replace("\r", "").split("\n")
    newlines = []
    style = None
    valid = {"*", "**", "***", "****", "+", "-"}
    # valid2 = {"* [ ]", "** [ ]", "*** [ ]", "**** [ ]"}  # TODO
    for line in lines:
        # util.dbgprint(str(repr(line)))
        if line == "":
            style = None
            newlines.append(line)
        else:
            parts = line.split(" ")
            if len(parts) > 1 and parts[0] in valid:
                style = parts[0]
                newlines.append(line)
            else:
                if style is not None:
                    newlines.append(style + " " + line)
                else:
                    newlines.append(line)

    howmanyemptylinestoappend = 4
    prependnewlinecount = 0
    appendnewlinecount = 0
    beg = True
    newlines2 = []
    for line in newlines:
        if beg:
            if line == "":
                prependnewlinecount += 1
            else:
                if prependnewlinecount < howmanyemptylinestoappend:
                    for i in range(howmanyemptylinestoappend - prependnewlinecount):
                        newlines2.append("")
                beg = False
        else:
            if line == "":
                appendnewlinecount += 1
            else:
                appendnewlinecount = 0
        newlines2.append(line)
    if appendnewlinecount < howmanyemptylinestoappend:
        for i in range(howmanyemptylinestoappend - appendnewlinecount):
            newlines2.append("")
    newplain = "\n".join(newlines2)
    return newplain


def convert_multiline_markup_string_into_safe_html(unsafe):
    # TODO: docstring

    # stackoverflow.com/questions/13938975/how-to-remove-indentation-from-an-unordered-list-item
    OPENING_UL_TAG = """<ul style=" margin: 0;  padding-left: 1.2em; " >"""

    def str_bold(s):
        # TODO: docstring
        inside_tag = False
        split_s = s.split("**")
        if len(split_s) % 2 == 0:
            # odd number of tags
            return s
        result = ""
        for component in split_s:
            if inside_tag:
                result += "<b>" + component + "</b>"
                inside_tag = False
            else:
                result += component
                inside_tag = True
        return result

    def str_ita(s):
        # TODO: docstring
        inside_tag = False
        split_s = s.split("***")
        if len(split_s) % 2 == 0:
            # odd number of tags
            return s
        result = ""
        for component in split_s:
            if inside_tag:
                result += "<i>" + component + "</i>"
                inside_tag = False
            else:
                result += component
                inside_tag = True
        return result

    def str_itabold(s):
        # TODO: docstring
        inside_tag = False
        split_s = s.split("****")
        if len(split_s) % 2 == 0:
            # odd number of tags
            return s
        result = ""
        for component in split_s:
            if inside_tag:
                result += "<b><i>" + component + "</i></b>"
                inside_tag = False
            else:
                result += component
                inside_tag = True
        return result

    def str_und(s):
        # TODO: docstring
        inside_tag = False
        split_s = s.split("__")
        if len(split_s) % 2 == 0:
            # odd number of tags
            return s
        result = ""
        for component in split_s:
            if inside_tag:
                result += "<u>" + component + "</u>"
                inside_tag = False
            else:
                result += component
                inside_tag = True
        return result

    def str_strike(s):
        # TODO: docstring
        inside_tag = False
        split_s = s.split("---")
        if len(split_s) % 2 == 0:
            # odd number of tags
            return s
        result = ""
        for component in split_s:
            if inside_tag:
                result += "<s>" + component + "</s>"
                inside_tag = False
            else:
                result += component
                inside_tag = True
        return result

    def str_markup(s):
        # TODO: docstring
        s = str_itabold(s)
        s = str_ita(s)
        s = str_bold(s)
        s = str_und(s)
        s = str_strike(s)
        return s

    def line_ahref(s):
        """ahref until space, lt, gt, quote, then escaped text"""
        link = ""
        rest = ""
        endlinkchar = {" ", '<', '>', '"', "'", }

        if s.startswith("http://") or s.startswith("https://") or s.startswith("www."):
            stilllink = True
            for i in range(len(s)):
                if s[i] in endlinkchar:
                    stilllink = False
                if stilllink:
                    link += s[i]
                else:
                    rest += s[i]
        else:
            rest = s

        rest_safe = html.escape(rest)
        rest_safe = str_markup(rest_safe)
        link_safe = html.escape(link)
        if link == "":
            return rest_safe
        else:
            return "<a href=\"" + link_safe + "\">" + link_safe + "</a>" + rest_safe

    def line_bullet(s):
        # TODO: docstring
        if s.startswith("* "):
            rest = s[2:]
            safe = line_ahref(rest)
            return OPENING_UL_TAG + "<li>" + safe + "</li></ul>"
        elif s.startswith("** "):
            rest = s[3:]
            safe = line_ahref(rest)
            return OPENING_UL_TAG + OPENING_UL_TAG + "<li>" + safe + "</li></ul>" + "</ul>"
        elif s.startswith("*** "):
            rest = s[4:]
            safe = line_ahref(rest)
            return OPENING_UL_TAG + OPENING_UL_TAG + OPENING_UL_TAG + "<li>" + safe + "</li></ul>" + "</ul>" + "</ul>"
        elif s.startswith("**** "):
            rest = s[5:]
            safe = line_ahref(rest)
            return OPENING_UL_TAG + OPENING_UL_TAG + OPENING_UL_TAG + OPENING_UL_TAG + "<li>" + safe + "</li></ul>" + "</ul>" + "</ul>" + "</ul>"
        else:
            return line_ahref(s)

    def multiline_deduplicate_ul(s):
        # TODO: docstring
        new = s.replace("</ul><br>\n" + OPENING_UL_TAG, "\n")  # join neighboring lists
        new = new.replace("</ul><br>\n", "</ul>\n")  # do not put <br> after the end of a list
        new = new.replace("</ul>\n" + OPENING_UL_TAG, "\n")  # join neighboring lists (without <br>)
        new = new.replace("</ul>\n" + OPENING_UL_TAG, "\n")  # join neighboring lists (without <br>)
        new = new.replace("</ul>\n" + OPENING_UL_TAG, "\n")  # join neighboring lists (without <br>)
        new = new.replace("</ul>\n" + OPENING_UL_TAG, "\n")  # join neighboring lists (without <br>)
        return new

    new = unsafe.replace("\r", "")

    lines = new.split("\n")
    new_lines = []
    for line in lines:
        new_line = line_bullet(line)
        new_lines.append(new_line)
    new = "\n".join(new_lines)
    new = new.replace("\n", "<br>\n")
    new = multiline_deduplicate_ul(new)

    return new


def multiline_markup_checkbox_mapping(markup, plain, edit_chkbox_state=False, chkbox_on_list=None,
                                      disabled_checkboxes=False):
    # TODO: docstring
    # """markup - the html-converted sanitized markup text
    #    plain - the plaintext source of the markup text
    #    edit_chkbox_state - if false, it returns html with html checkboxes, if true, it takes chkbox_on_list and makes those checked and the rest unchecked and returns the modified plain text
    # """
    # TODO: better docstring
    if chkbox_on_list is None:
        chkbox_on_list = []

    def chkbox_name(index):
        return "checkbox" + str(index)

    def chkbox_html(index, checked):
        attr_chkd = ""
        if checked:
            attr_chkd = "checked=\"checked\""
        attr_disabled = ""
        if disabled_checkboxes:
            attr_disabled = """ disabled="disabled" """
        return "<input type=\"checkbox\" name=\"" + chkbox_name(index) + "\" " + attr_chkd + " " + attr_disabled + ">"

    checkbox_index = 0
    result_html_list = []
    plain_edit_list = []

    # go through [ ]/[x]
    markup_left_bracket_split = markup.split("[")
    plain_left_bracket_split = plain.split("[")
    component_pairs_left_bracket_split = zip(markup_left_bracket_split, plain_left_bracket_split)
    for component_pair in component_pairs_left_bracket_split:
        component_markup, component_plain = component_pair
        component_markup_rest = component_markup[2:]
        component_plain_rest = component_plain[2:]
        if checkbox_index == 0:
            result_html_list.append(component_markup)
            plain_edit_list.append(component_plain)
            checkbox_index += 1
            continue
        if component_markup.startswith(" ]"):
            result_html_list.append(chkbox_html(checkbox_index, False))
            result_html_list.append(component_markup_rest)
            if chkbox_name(checkbox_index) in chkbox_on_list:
                plain_edit_list.append("[x]" + component_plain_rest)
            else:
                plain_edit_list.append("[ ]" + component_plain_rest)
        elif component_markup.startswith("x]"):
            result_html_list.append(chkbox_html(checkbox_index, True))
            result_html_list.append(component_markup_rest)
            if chkbox_name(checkbox_index) in chkbox_on_list:
                plain_edit_list.append("[x]" + component_plain_rest)
            else:
                plain_edit_list.append("[ ]" + component_plain_rest)
        else:
            # no checkbox
            result_html_list.append("[" + component_markup)
            plain_edit_list.append("[" + component_plain)
        checkbox_index += 1

    # info: one checkbox number is lost here because the for loop increments after the last item

    plain_edit = "".join(plain_edit_list)
    result_html = "".join(result_html_list)
    result_html_list = []
    plain_edit_list = []
    checkbox_index_begin_secondphase = checkbox_index

    # go through +/-
    markup_newline_split = result_html.split("\n")
    plain_newline_split = plain_edit.split("\n")

    component_pairs_newline_split = zip(markup_newline_split, plain_newline_split)
    for component_pair in component_pairs_newline_split:
        component_markup, component_plain = component_pair
        component_markup_rest = component_markup[2:]
        component_plain_rest = component_plain[2:]
        if checkbox_index == checkbox_index_begin_secondphase:
            result_html_list.append(component_markup)
            plain_edit_list.append(component_plain)
            checkbox_index += 1
            continue
        if component_markup.startswith("- "):
            result_html_list.append("\n" + chkbox_html(checkbox_index, False))
            result_html_list.append(component_markup_rest)
            if chkbox_name(checkbox_index) in chkbox_on_list:
                plain_edit_list.append("\n+ " + component_plain_rest)
            else:
                plain_edit_list.append("\n- " + component_plain_rest)
        elif component_markup.startswith("+ "):
            result_html_list.append("\n" + chkbox_html(checkbox_index, True))
            result_html_list.append(component_markup_rest)
            if chkbox_name(checkbox_index) in chkbox_on_list:
                plain_edit_list.append("\n+ " + component_plain_rest)
            else:
                plain_edit_list.append("\n- " + component_plain_rest)
        else:
            # no checkbox
            result_html_list.append("\n" + component_markup)
            plain_edit_list.append("\n" + component_plain)
        checkbox_index += 1

    plain_edit = "".join(plain_edit_list)
    result_html = "".join(result_html_list)

    if edit_chkbox_state:
        return plain_edit
    return result_html


def convert_multiline_string_into_safe_html_short_snippet(unsafe, len):
    # TODO: docstring
    """Any markup is ignored, the output is just plain text and unicode "return" symbols."""
    new = unsafe.strip().replace("\n",
                                 "↵")  # http://stackoverflow.com/questions/18927672/newline-symbol-unicode-character
    new = new.replace("\r", "")
    new = new[0:len + 1]
    new = html.escape(new)
    return new


# def read_pem_cert_fingerprint(path_to_pem):
#     """Returns the sha256 string fingerprint of the SSL cert"""
#     from OpenSSL.crypto import load_certificate, FILETYPE_PEM
#
#     cert_file_string = open(path_to_pem, "rb").read()
#     cert = load_certificate(FILETYPE_PEM, cert_file_string)
#
#     sha256_fingerprint = cert.digest("sha256")
#     dbgprint(sha256_fingerprint)
#     return sha256_fingerprint

def safe_string_compare(string1, string2):
    # TODO: docstring
    """Safe comparison to avoid timing attacks"""
    # hashing&salting so that string comparison doesn't easily allow timing attacks
    random_string = create_id_task()
    hash1 = hashlib.sha256(repr(string1 + random_string).encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(repr(string2 + random_string).encode("utf-8")).hexdigest()
    assert len(hash1) == 64
    assert len(hash2) == 64
    return hash1 == hash2


def tasks_backup(task_store, task_store_trash, s=None):
    # TODO: docstring
    """Creates a backup of the internal task database and trash. The optional s parameter allows appending a string to the file names of the backup."""
    timestamp = current_timestamp().replace(":", "-").replace(" ", "_")
    if s is not None:
        timestamp += "_" + str(s)
    task_store.task_store_save(
        alt_path=os.path.join(config.PATH_SAVE_DB_BACKUP, "woolbackup_" + timestamp + "_" + config.FILE_TASKS_DAT))
    task_store_trash.task_store_save(
        alt_path=os.path.join(config.PATH_SAVE_DB_BACKUP, "woolbackup_" + timestamp + "_" + config.FILE_TASKS_TRASH_DAT))

