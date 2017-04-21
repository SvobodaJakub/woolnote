# University of Illinois/NCSA Open Source License
# Copyright (c) 2017, Jakub Svoboda.

# TODO: docstring for the file

# constants for HTML contents
#############################

# in a separate file because of licensing and because it's nicer
from woolnote.html_constants_css_uikit_2_27_1 import CSS_UIKIT_2_27_1_STYLE_OFFLINE, HTML_UIKIT_2_27_1_STYLE_OFFLINE

HTML_VIEWPORT_META = """<meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0, user-scalable=no, user-scalable=0"/>"""

# the class uk-button ignores span's font size but when uikit is not loaded (need to use uk-button uk-button-large), the span at least still conveys the info that this should be big
HTML_SPAN_STYLE_BIG = "style=\"font-size:20pt; \""

HTML_NOTE_LINK_WITH_PREVIEW = """
<a href="/woolnote?{request_params}" style="text-decoration: none"  ><div>{sanitized_task_name}{sanitized_due_date}<br>
<small><small>{sanitized_task_folder}; {sanitized_task_tags}</small></small><br>
<small>{sanitized_body_snippet}</small></div></a><hr>
""".strip()

HTML_JS_EVENT_TEXTAREA_RESIZE = "if (document.getElementById('TaTb').scrollHeight > document.getElementById('TaTb').clientHeight) {document.getElementById('TaTb').style.height = (document.getElementById('TaTb').scrollHeight + 10) + 'px'; } "

HTML_ELEM_ATTR_JS_EVENTS_TEXTAREA_RESIZE = """ onclick="{js_event_textarea}" oninput="{js_event_textarea}" onfocus="{js_event_textarea}" onmouseover="{js_event_textarea}" onscroll="{js_event_textarea}" onmousemove="{js_event_textarea}" onmouseenter="{js_event_textarea}" onload="{js_event_textarea}" onpageshow="{js_event_textarea}" onwheel="{js_event_textarea}" ontouchstart="{js_event_textarea}" ontouchmove="{js_event_textarea}"  """.format(
    js_event_textarea=HTML_JS_EVENT_TEXTAREA_RESIZE)

HTML_UIKIT_LINK_REL_ONLINE = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/uikit/2.15.0/css/uikit.gradient.min.css">"""
HTML_UIKIT_2_27_1_LINK_REL_LOCAL = """<link rel="stylesheet" href="../uikit-2.27.1.gradient-customized.css.v5.css">"""  # increasing number because of caching&development

# with edits (comments in css):
# the "\" characters had to be escaped in the css (due to Python evaluating \somecode to unicode chars in the string)


