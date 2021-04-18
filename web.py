"""Search engine web server."""

import tiny
from flask import Flask, render_template, request

my_index = tiny.Index("sample")
app = Flask(__name__)

@app.route("/")
def root():
    return render_template("index.html")

@app.route("/search")
def search():
    q = request.args['q']
    results = my_index.search(q,"sample")
    return render_template("results.html", q=q, results=results)

if __name__ == '__main__':
    import sys
    make_index(sys.argv[1])
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
