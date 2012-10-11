#!/usr/bin/env python
# Copyright (C) 2010-2012 Cuckoo Sandbox Developers.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import os
import sys
import logging
from jinja2.loaders import FileSystemLoader
from jinja2.environment import Environment
from bottle import route, run, static_file, redirect, request, HTTPError

logging.basicConfig()
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

from lib.cuckoo.core.database import Database
from lib.cuckoo.common.constants import CUCKOO_ROOT
from lib.cuckoo.common.utils import store_temp_file

env = Environment()
env.loader = FileSystemLoader(os.path.join(CUCKOO_ROOT, "data", "html"))

@route("/")
def index():
    context = {}
    template = env.get_template("submit.html")
    return template.render({"context" : context})

@route("/browse")
def browse():
    db = Database()

    rows = db.list()
    template = env.get_template("browse.html")

    return template.render({"rows" : rows, "os" : os})

@route("/static/<filename:path>")
def server_static(filename):
    return static_file(filename, root=os.path.join(CUCKOO_ROOT, "data", "html"))

@route("/submit", method="POST")
def submit():
    context = {}
    errors = False

    package  = request.forms.get("package", "")
    options  = request.forms.get("options", "")
    priority = request.forms.get("priority", 1)
    timeout  = request.forms.get("timeout", "")
    data = request.files.file

    try:
        priority = int(priority)
    except ValueError:
        context["error_toggle"] = True
        context["error_priority"] = "Needs to be a number"
        errors = True

    if data == None or data == "":
        context["error_toggle"] = True
        context["error_file"] = "Mandatory"
        errors = True

    if errors:
        template = env.get_template("submit.html")
        return template.render({"timeout" : timeout,
                                "priority" : priority,
                                "options" : options,
                                "package" : package,
                                "context" : context})

    temp_file_path = store_temp_file(data.file.read(), data.filename)

    db = Database()
    task_id= db.add_path(file_path=temp_file_path,
                         timeout=timeout,
                         priority=priority,
                         options=options,
                         package=package)

    template = env.get_template("success.html")
    return template.render({"taskid" : task_id,
                            "submitfile" : data.filename.decode("utf-8")})

@route("/view/<task_id>")
def view(task_id):
    if not task_id.isdigit():
        return HTTPError(code=404, output="The specified ID is invalid")

    report_path = os.path.join(CUCKOO_ROOT, "storage", "analyses", task_id, "reports", "report.html")

    if not os.path.exists(report_path):
        return HTTPError(code=404, output="Report not found")

    return open(report_path, "rb").read()

if __name__ == "__main__":
    run(host="0.0.0.0", port=8080, reloader=True)
