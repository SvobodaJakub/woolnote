# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

from woolnote import systemencoding
import functools
import pickle

# Note: It's best to record the tests in tmpfs so that all the writes don't go to the disk.
# TODO: make the test friendlier to SSD/HDD - dump the pickle data only after ctrl-c

# False - no tests can be recorded nor replayed; True - tests can be recorded and replayed
TEST_FRAMEWORK_ENABLED = False

# False - tests are recorded; True - tests are replayed
PICKLETEST_REPLAY = False

# tests that generate/read pickled data to test functions and methods in the context of the program's state
PICKLETEST_ENABLED = True
PICKLETEST_PRINT_STATUS_INSIDE_EXEC = False
PICKLETEST_OUTFILE = "PICKLETEST_OUTFILE.txt"
PICKLETEST_REPLAY_STATUS_EXPECTED = "PICKLETEST_REPLAY_STATUS_EXPECTED.txt"
PICKLETEST_REPLAY_STATUS_OBSERVED = "PICKLETEST_REPLAY_STATUS_OBSERVED.txt"
PICKLETEST_PICKLE_FILENAME_BEGINNING = "PICKLETEST_PICKLE"

# tests that generate python code to do integration testing through the whole woolnote's stack
TEST_GEN_SERIALIZABLE_OUTFILE = "TEST_GEN_SERIALIZABLE_OUTFILE.txt"
TEST_GEN_SERIALIZABLE_OUTFILE_REPLAY = False

# dict[test_suite string, WoolTest instance]
test_suite_instances = {}


class WoolTest():
    def __init__(self, test_suite):
        # test_suite = identifier of the integration test graph.

        # Why `test_suite` identifier is useful:
        # When a certain test-decorated method is recorded and tested, it may call other test-decorated methods
        # during its execution. Only the top-level calls into the call graph are recorded and later replayed
        # (because replaying only parts of the call graph would re-execute some parts and would desynchronize the
        # app state and practically break everything into untestable mess). That being said, there are multiple
        # directions or perspectives from which to perform integration tests. When a method or function is a
        # top-level call under the given `test_suite` identifier, it is then recorded and replayed under that
        # test suite and ignored under other test suites where it is not a top-level call (where it is called by
        # other test-decorated functions).
        super().__init__()

        self.test_suite = test_suite

        # if True, inhibit saving of decorated functions to pickle
        self.replaying_integration = False

        # if a decorated function is executed, this is set to True, so that it is known when other decorated functions are called during its execution; it's set to False upon return of the originally-called function
        self.already_inside_execution = False

        # dict[fun name, fun pointer]
        # because method pointers can't be pickled
        self.function_pointers = {}

        # watched instances
        # set(tuple[instance id (any type that can be used as index and pickled, e.g. str), instance pointer])
        self.instances = set()

        # list of tuples (function name, has_self, args, kwargs, returned data) where each var in the tuple is byte pickle dump
        self.chronology = []

        # this will be pickled as is, other parts of the program can add data that should be pickled here for testing purposes
        # intended for data immediately pickled using pickle.dumps()
        self.other_pickled_data = {}

        # this will be pickled as is, other parts of the program can add data that should be pickled here for testing purposes
        # intended for data saved as references so that the latest state is then pickled
        self.other_referenced_data = {}

    def pickle_filename(self):
        if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
            raise Exception("test framework disabled")
        return PICKLETEST_PICKLE_FILENAME_BEGINNING + "_" + str(self.test_suite) + ".dat"

    def pickle_dump(self):
        if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
            raise Exception("test framework disabled")
        if not self.replaying_integration and not PICKLETEST_REPLAY:
            with open(self.pickle_filename(), 'wb') as f:
                # yes, dumping all over and over again each time a decorated func is called
                # the bright side is that it is simple and always shows the most current state
                pickle.dump((self.chronology, self.other_pickled_data, self.other_referenced_data), f)

    def integration(self, has_self=False):

        def actual_decorator(func):
            if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
                return func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
                    return func(*args, **kwargs)
                with open(PICKLETEST_OUTFILE, 'a', encoding="utf-8", newline="\n") as f:
                    is_watched_instance = has_self and args[0] in {x[1] for x in self.instances}
                    is_interesting_for_logging = is_watched_instance or not has_self
                    instance_id = next((x[0] for x in self.instances if args[0] == x[1])) if is_watched_instance else None
                    if is_interesting_for_logging and (PICKLETEST_PRINT_STATUS_INSIDE_EXEC or not self.already_inside_execution):
                        f.write("\n")
                        f.write("already_inside_execution: {}\n".format(repr(self.already_inside_execution)))
                        f.write("function name: {}\n".format(func.__name__))
                        if has_self:
                            # strip `self` from args
                            f.write("args: {}\n".format(repr(args[1:])))
                        else:
                            f.write("args: {}\n".format(repr(args)))
                        f.write("kwargs: {}\n".format(repr(kwargs)))
                    if not self.already_inside_execution:
                        if has_self:
                            # strip `self` from args
                            pickle_args = pickle.dumps(args[1:])
                        else:
                            pickle_args = pickle.dumps(args)
                        pickle_kwargs = pickle.dumps(kwargs)
                    if is_interesting_for_logging:
                        already_inside_execution_orig_value = self.already_inside_execution
                        self.already_inside_execution = True
                    e = None
                    try:
                        ret = func(*args, **kwargs)
                    except Exception as ex:
                        ret = "Exception raised - {}".format(repr(ex))
                        e = ex
                    if is_interesting_for_logging:
                        self.already_inside_execution = already_inside_execution_orig_value
                    if is_interesting_for_logging and not self.already_inside_execution:
                        pickle_ret = pickle.dumps(ret)
                        self.chronology.append((func.__name__, instance_id, has_self, pickle_args, pickle_kwargs, pickle_ret))
                    if is_interesting_for_logging and (PICKLETEST_PRINT_STATUS_INSIDE_EXEC or not self.already_inside_execution):
                        f.write("return value: {}\n".format(repr(ret)))
                if not self.replaying_integration and not PICKLETEST_REPLAY:
                    self.pickle_dump()
                if e:
                    raise e
                return ret

            # save pointer to the decorated function so that it can be called decorated and we can get the debug output
            if func.__name__ in self.function_pointers:
                raise Exception("There are two functions with the same name: {}".format(func.__name__))
            self.function_pointers[func.__name__] = wrapper
            return wrapper
        return actual_decorator

    def pre_rerun_integration(self):
        if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
            raise Exception("test framework disabled")
        with open(self.pickle_filename(), 'rb') as f:
            _, replay_other_pickled_data, replay_other_referenced_data = pickle.load(f)
        self.other_pickled_data.update(replay_other_pickled_data)
        self.other_referenced_data.update(replay_other_referenced_data)

    def rerun_integration(self):
        if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
            raise Exception("test framework disabled")
        replaying_integration_orig_value = self.replaying_integration
        with open(self.pickle_filename(), 'rb') as f:
            replay_chronology, _, _ = pickle.load(f)
        self.replaying_integration = True
        # recording replay status into two files so that it can be diffed nicely
        with open(PICKLETEST_REPLAY_STATUS_EXPECTED, 'a', encoding="utf-8", newline="\n") as fe:
            with open(PICKLETEST_REPLAY_STATUS_OBSERVED, 'a', encoding="utf-8", newline="\n") as fo:
                for func_name, instance_id, has_self, pickle_args, pickle_kwargs, pickle_ret in replay_chronology:
                    args = list(pickle.loads(pickle_args))
                    kwargs = pickle.loads(pickle_kwargs)
                    expected_ret = pickle.loads(pickle_ret)
                    func = self.function_pointers[func_name]
                    if has_self:
                        found_self = next((x[1] for x in self.instances if x[0] == instance_id))
                        args[0:0] = [found_self]
                    # printing calls and returns so that nested calls are visible and if it crashes, there's at least some info
                    fe.write("\n")
                    fe.write("[call   {}]\n".format(func.__name__))
                    fo.write("\n")
                    fo.write("[call   {}]\n".format(func.__name__))
                    try:
                        ret = func(*args, **kwargs)
                    except Exception as e:
                        ret = "Exception raised - {}".format(repr(e))
                    fe.write("[return {}]\n".format(func.__name__))
                    fo.write("[return {}]\n".format(func.__name__))
                    # printing in one run so that nested calls print nicely
                    fe.write("\n")
                    fe.write("function name: {}\n".format(func.__name__))
                    fe.write("instance_id: {}\n".format(repr(instance_id)))
                    fe.write("test_suite: {}\n".format(repr(self.test_suite)))
                    fe.write("has_self: {}\n".format(repr(has_self)))
                    fe.write("args: {}\n".format(repr(args)))
                    fe.write("kwargs: {}\n".format(repr(kwargs)))
                    fe.write("return value: {}\n".format(repr(expected_ret)))
                    fo.write("\n")
                    fo.write("function name: {}\n".format(func.__name__))
                    fo.write("instance_id: {}\n".format(repr(instance_id)))
                    fo.write("test_suite: {}\n".format(repr(self.test_suite)))
                    fo.write("has_self: {}\n".format(repr(has_self)))
                    fo.write("args: {}\n".format(repr(args)))
                    fo.write("kwargs: {}\n".format(repr(kwargs)))
                    fo.write("return value: {}\n".format(repr(ret)))
                    fe.write("return values match: {}\n".format(repr(True)))
                    fo.write("return values match: {}\n".format(repr(ret == expected_ret)))
                    # assert ret == expected_ret  # TODO uncomment if you want it to crash at the first difference
        self.replaying_integration = replaying_integration_orig_value


def get_test_suite_instance(test_suite):
    if test_suite not in test_suite_instances:
        test_suite_instances[test_suite] = WoolTest(test_suite)
    return test_suite_instances[test_suite]


def integration_function(test_suite):
    wooltest = get_test_suite_instance(test_suite)
    return wooltest.integration(has_self=False)


def integration_method(test_suite):
    wooltest = get_test_suite_instance(test_suite)
    return wooltest.integration(has_self=True)


def integration_instance(test_suite, instance_id, instance_ref):
    if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
        return
    wooltest = get_test_suite_instance(test_suite)
    wooltest.instances.add((instance_id, instance_ref))


def integration_pre_rerun(test_suite):
    if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
        raise Exception("test framework disabled")
    # loads self.other_pickled_data and self.other_referenced_data from the pickle file
    wooltest = get_test_suite_instance(test_suite)
    wooltest.pre_rerun_integration()


def integration_rerun(test_suite):
    if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
        raise Exception("test framework disabled")
    # loads self.chronology from the pickle file and replays the calls
    # note that it might be necessary to COMPLETELY replicate the whole environment for the test to result in an identical run
    wooltest = get_test_suite_instance(test_suite)
    wooltest.rerun_integration()


def integration_pickle_data(test_suite, key, value):
    if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
        return
    # pickling right away so that if the data changes later, the recorded version stays as it was
    # use this to save auxiliary data when you need the earliest state to be preserved
    wooltest = get_test_suite_instance(test_suite)
    wooltest.other_pickled_data[key] = pickle.dumps(value)


def integration_unpickle_data(test_suite, key):
    if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
        raise Exception("test framework disabled")
    wooltest = get_test_suite_instance(test_suite)
    return pickle.loads(wooltest.other_pickled_data[key])


def integration_referenced_data(test_suite):
    if not TEST_FRAMEWORK_ENABLED or not PICKLETEST_ENABLED :
        return {}
    # use this to save auxiliary data when you need the latest state to be preserved
    wooltest = get_test_suite_instance(test_suite)
    return wooltest.other_referenced_data


def tests_deterministic_replacement(replacement_func):
    if not TEST_FRAMEWORK_ENABLED:
        def decor(func):
            return func
        return decor
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return replacement_func(*args, **kwargs)
        return wrapper
    return decorator


class GenTest():
    def __init__(self):
        # if a decorated function is executed, this is set to True, so that it is known when other decorated functions are called during its execution; it's set to False upon return of the originally-called function
        self.already_inside_execution = False

        # watched instances
        # set(tuple[instance id (any type that can be used as index and pickled, e.g. str), instance pointer])
        self.instances = set()
    def capture_function_with_serializable_in_out(self, has_self=False):

        def actual_decorator(func):
            if not TEST_FRAMEWORK_ENABLED:
                return func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not TEST_FRAMEWORK_ENABLED or TEST_GEN_SERIALIZABLE_OUTFILE_REPLAY:
                    return func(*args, **kwargs)
                with open(TEST_GEN_SERIALIZABLE_OUTFILE, 'a', encoding="utf-8", newline="\n") as f:
                    is_watched_instance = has_self and args[0] in {x[1] for x in self.instances}
                    is_interesting_for_logging = (is_watched_instance or not has_self) and not self.already_inside_execution
                    instance_id = next((x[0] for x in self.instances if args[0] == x[1])) if is_watched_instance else None
                    if is_interesting_for_logging:
                        f.write("\n")
                        if has_self:
                            f.write("instance_self = get_instance_self({})\n".format(repr(instance_id)))
                            # strip `self` from args
                            f.write("args = {}\n".format(repr(args[1:])))
                        else:
                            f.write("args = {}\n".format(repr(args)))
                        f.write("kwargs = {}\n".format(repr(kwargs)))
                        f.write("function = instance_self.{}\n".format(func.__name__))
                        already_inside_execution_orig_value = self.already_inside_execution
                        self.already_inside_execution = True
                    e = None
                    try:
                        ret = func(*args, **kwargs)
                    except Exception as ex:
                        ret = "Exception raised - {}".format(repr(ex))
                        e = ex
                    if is_interesting_for_logging:
                        self.already_inside_execution = already_inside_execution_orig_value
                        f.write("expected = {}\n".format(repr(ret)))
                        f.write("try:\n")
                        f.write("    output = function(*args, **kwargs)\n")
                        f.write("except Exception as ex:\n")
                        f.write('''    output = "Exception raised - {}".format(repr(ex))\n''')
                        f.write('''assert output == expected, "{} != {}".format(repr(output), repr(expected))\n''')
                        f.write("\n")
                if e:
                    raise e
                return ret

            return wrapper
        return actual_decorator

gen_test = GenTest()

def gen_serializable_test_function():
    return gen_test.capture_function_with_serializable_in_out(has_self=False)

def gen_serializable_test_method():
    return gen_test.capture_function_with_serializable_in_out(has_self=True)

def gen_serializable_test_instance(instance_id, instance_ref):
    if not TEST_FRAMEWORK_ENABLED:
        return
    gen_test.instances.add((instance_id, instance_ref))

def gen_serializable_test_new_request():
    if not TEST_FRAMEWORK_ENABLED or TEST_GEN_SERIALIZABLE_OUTFILE_REPLAY:
        return
    with open(TEST_GEN_SERIALIZABLE_OUTFILE, 'a', encoding="utf-8", newline="\n") as f:
        f.write("regenerate_WebInterfaceHandlerLocal()\n")

def gen_serializable_test_beginning():
    if not TEST_FRAMEWORK_ENABLED or TEST_GEN_SERIALIZABLE_OUTFILE_REPLAY:
        return
    with open(TEST_GEN_SERIALIZABLE_OUTFILE, 'a', encoding="utf-8", newline="\n") as f:
        beg = """
# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

# tests must be imported and set up early so that the deterministic function replacements are active
from woolnote import tests

tests.TEST_FRAMEWORK_ENABLED = True
tests.TEST_GEN_SERIALIZABLE_OUTFILE_REPLAY = True  # set to False to regenerate the same tests, useful after changes and careful deleting of failing asserts in the old tests
tests.PICKLETEST_REPLAY = False
tests.PICKLETEST_ENABLED = False
# uncomment to generate other tests from this integration test
# tests.PICKLETEST_ENABLED = True

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

task_store = TaskStoreTestingNoWrite("./TEST_tasks.dat")
task_store_trash = TaskStoreTestingNoWrite("./TEST_tasks_trash.dat")

task_store.task_store_load()
task_store_trash.task_store_load()
util.tasks_backup(task_store, task_store_trash)

ui_auth = WoolnoteUIAuth()
woolnote_config = WoolnoteConfig()
ui_backend = UIBackend(task_store, task_store_trash)
web_ui = WebUI(task_store, task_store_trash, ui_backend, woolnote_config, ui_auth)

# uncomment to generate other tests from this integration test
# tests.integration_instance("web_ui", "web_ui", web_ui)
# tests.integration_instance("web_ui", "woolnote_config", woolnote_config)
# tests.integration_instance("web_ui", "ui_auth", ui_auth)

WebInterfaceHandlerLocal = get_WebInterfaceHandlerLocal(woolnote_config, task_store, web_ui, ui_auth)

def regenerate_WebInterfaceHandlerLocal():
    # Each instance is used for only one request, not interested in the previous instances.
    tests.gen_test.instances = set()

    # Let it initialize a bit, it doesn't matter that the super().__init__() call in __init__() fails, the `self` object
    # will exist nonetheless, and it will suffice for our tests.
    try:
        WebInterfaceHandlerLocal()
    except:
        pass

def get_instance_self(string):
    reference = next((x[1] for x in tests.gen_test.instances if string == x[0]))
    return reference

        """.strip()
        f.write(beg)
        f.write("\n")
        f.write("\n")
        f.write("\n")

