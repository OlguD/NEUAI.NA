from flask import render_template, Response, request, jsonify, send_file
import json
import os
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

@app.route('/find_student')
def find_student():
    school_number = request.headers.get("X-School-Number")
    try:
        image_path = FindStudent.find_by_school_number(school_number)
        
        # Try to find student details from studentData.json
        student_data = {}
        student_data_path = os.path.join(app.static_folder, 'studentData', 'studentData.json')
        
        if os.path.exists(student_data_path):
            try:
                with open(student_data_path, 'r', encoding='utf-8') as f:
                    student_data_list = json.load(f)
                    
                # Try to find the student by school number
                for student in student_data_list:
                    if str(student.get('schoolNumber', '')) == school_number or str(student.get('studentNumber', '')) == school_number:
                        student_data = student
                        break
            except Exception as e:
                print(f"Error reading student data: {e}")
        
        return jsonify({
            "image_path": image_path,
            "student_data": student_data
        })

    except Exception as e:
        return jsonify({"error": str(e)})