"""
@title
@description
"""

from bokeh.embed import server_document
from flask import render_template


def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template('index.html', script=script, template="Flask")
