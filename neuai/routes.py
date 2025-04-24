from flask import render_template, Response, request, jsonify
from neuai import app

@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/system')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['POST'])
def get_data():
    data = request.get_json()
    # Process the data and return a response
    return jsonify({'message': 'Data received', 'data': data})