#!/usr/bin/python 
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, json

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/apptest', methods = ['GET'])
def apptest():
    return render_template('apptest.html') 


@app.route('/planning_interface', methods = ['GET'])
def plannin_interface():
    return render_template('planning.html') 

@app.route('/planning_auto', methods = ['POST'])
def planning_auto():
    if request.headers['Content-Type'] == 'application/json':
        return json.dumps(request.json)
    else:
        return "415 Unsupported Media Type ;)"

if __name__ == '__main__':
    app.run(debug = True)
