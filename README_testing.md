Woolnote tests

* `tests_integration.py` - Simulating whole web interface sessions and checking the responses for being bit-exact as what's expected. Can be used to regenerate itself and other tests.
* `PICKLETEST*`, `run_tests*.py` - Tests of selected parts of Woolnote. `pickle` is used to store inputs and expected outputs and auxiliary data for the tested functions.
* `TEST_tasks*.dat` - Special versions of the task database that contains tasks that are used in the integration tests repeatedly. When the integration tests run, writing in the task stores is disabled, so that changes are lost upon the completion of the tests.
* `woolnote/tests.py` - A custom testing "framework" that enables the described tests. It mainly works by hooking the decorated tested functions/methods and recording their class instances, inputs, and outputs. When replaying the tests, the testing framework already has references to the instantiated methods in the initialized Woolnote app and can call them in such a way that their class instances they exist in are preserved and connected to each other just like during a normal Woolnote run, eliminating the need for testing fixtures and mocks like in a traditional testing framework (I am lazy).

Re-testing the app after changes

1. `python3 tests_integration.py`
    * This checks that the app as a whole behaves as expected. If there is something broken in one of the layers somewhere in the middle, the integration test crashes, but it might not be immediately evident why.
    * It is possible to tweak the code to regenerate pickletests (see below) - see comments in `tests_integration.py`.
    * It is possible to tweak the code to regenerate itself into `TEST_GEN_SERIALIZABLE_OUTFILE.txt`. This is useful after breaking changes - carefully check and uncomment the asserts in `tests_integration.py` where you made the breaking changes; after you go through all the breaking changes and `tests_integration.py` runs successfully, let it regenerate itself, which will re-generate the asserts with the new expected values. Then `mv TEST_GEN_SERIALIZABLE_OUTFILE.txt tests_integration.py`.
2. `python3 run_tests_replay_pickletest.py`
    * Runs selected parts of the Woolnote app more or less in isolation to help pinpoint regressions more precisely than `tests_integration.py`. This is done by having pickled auxiliary data for the tested functions, their inputs and outputs and comparing the actual output to the expected pickled output.
    * **Do not run these tests from untrusted sources.** Usually, you should generate the pickled tests yourself from a good working Woolnote version and use it during development to catch regressions early. After you finish with the new version, delete the pickled tests and regenerate them using `tests_integration.py`.
    * **Do not regenerate pickletests on an SSD.** The file-writing routine is extremely badly written and will write **lots** of data. Run it in a ramdisk.
    * If you need the pickletests to crash on the first difference (so that you don't have to `meld` the outputs every time), there's an assert for that (`# assert ret == expected_ret  # TODO uncomment if you want it to crash at the first difference`).
3. `meld PICKLETEST_REPLAY_STATUS_*`
    * Diff these files to see what changes happened between the Woolnote versions that generated the tests and the current version. The only differences you see should be those you did purposefully, anything else are regressions.
4. `bash TEST_reset_tasks_dat.sh`
    * Run this to delete the temporary .txt files.
