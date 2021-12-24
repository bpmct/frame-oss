from flask import Flask, render_template, redirect, abort

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("homepage.html")

@app.route('/<path:text>', methods=['GET', 'POST'])
def all_routes(text):
    if text.startswith('f'):
        # before we have a database haha
        if text == "fjsyDoKNNo":
            return render_template("frame.html")
        else:
            abort(404)
    else:
        abort(404)