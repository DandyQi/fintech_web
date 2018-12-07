from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/result')
def result():
    return render_template("result.html")


@app.route('/statistics')
def stat():
    return render_template("stats.html")


@app.route('/graphic')
def graphic():
    return render_template("graphic.html")


if __name__ == '__main__':
    app.run()
