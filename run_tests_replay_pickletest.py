# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.


"""
Woolnote note-taking web app. You can start it by running this file. The interface is at the configured port.
"""

# run with these environment variables: PYTHONIOENCODING=utf-8 PYTHONUTF8=1

from woolnote import tests
tests.TEST_FRAMEWORK_ENABLED = True
tests.PICKLETEST_REPLAY = True

# this runs Woolnote
import woolnote.woolnote

