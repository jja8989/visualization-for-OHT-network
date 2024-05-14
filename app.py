from flask import Flask, render_template, g
from db_setup import get_db

app = Flask(__name__)
app.secret_key  = 'e4e068348286cd74fb5cf4a996d88d72d0756357c848ca1a'

from func import bp                                             
app.register_blueprint(bp)                                     

@app.before_request                
def before_request():
    g.db = get_db()

@app.teardown_appcontext           
def teardown_db(exc):
    db = g.pop('db', None)       

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)