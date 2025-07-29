# -*- coding: utf-8 -*-
"""
Flask REST API Server with Supabase CRUD operations
학생 관리를 위한 REST API 서버
"""

from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# Flask 앱 초기화
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSON에서 한글 문자 지원

# Supabase 설정
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 에러 응답 헬퍼 함수
def error_response(message, status_code=400):
    return jsonify({"error": message}), status_code

def success_response(data, message="Success"):
    return jsonify({"message": message, "data": data})

# 1. 모든 학생 조회 (GET /students)
@app.route('/students', methods=['GET'])
def get_all_students():
    try:
        result = supabase.table('students').select('*').order('id').execute()
        students = result.data
        return success_response(students, "All students retrieved successfully")
    except Exception as e:
        return error_response(f"Failed to retrieve students: {str(e)}", 500)

# 2. 특정 학생 조회 (GET /students/<id>)
@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    try:
        result = supabase.table('students').select('*').eq('id', student_id).execute()
        students = result.data
        
        if not students:
            return error_response(f"Student with ID {student_id} not found", 404)
        
        return success_response(students[0], "Student retrieved successfully")
    except Exception as e:
        return error_response(f"Failed to retrieve student: {str(e)}", 500)

# 3. 새 학생 추가 (POST /students)
@app.route('/students', methods=['POST'])
def create_student():
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['name', 'age', 'grade']
        for field in required_fields:
            if field not in data:
                return error_response(f"Required field missing: {field}")
        
        # 데이터 삽입
        student_data = {
            'name': data['name'],
            'age': data['age'],
            'grade': data['grade']
        }
        
        result = supabase.table('students').insert(student_data).execute()
        
        if result.data:
            return success_response(result.data[0], "Student created successfully"), 201
        else:
            return error_response("Failed to create student", 500)
            
    except Exception as e:
        return error_response(f"Failed to create student: {str(e)}", 500)

# 4. 학생 정보 수정 (PUT /students/<id>)
@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        data = request.get_json()
        
        # 기존 학생 존재 확인
        result = supabase.table('students').select('*').eq('id', student_id).execute()
        if not result.data:
            return error_response(f"Student with ID {student_id} not found", 404)
        
        # 수정할 데이터 준비
        update_data = {}
        allowed_fields = ['name', 'age', 'grade']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return error_response("No data to update")
        
        # 데이터 수정
        result = supabase.table('students').update(update_data).eq('id', student_id).execute()
        
        if result.data:
            return success_response(result.data[0], "Student updated successfully")
        else:
            return error_response("Failed to update student", 500)
            
    except Exception as e:
        return error_response(f"Failed to update student: {str(e)}", 500)

# 5. 학생 정보 삭제 (DELETE /students/<id>)
@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        # 삭제 전 학생 존재 확인
        result = supabase.table('students').select('name').eq('id', student_id).execute()
        if not result.data:
            return error_response(f"Student with ID {student_id} not found", 404)
        
        student_name = result.data[0]['name']
        
        # 학생 정보 삭제
        result = supabase.table('students').delete().eq('id', student_id).execute()
        
        if result.data:
            return success_response({"id": student_id, "name": student_name}, "Student deleted successfully")
        else:
            return error_response("Failed to delete student", 500)
            
    except Exception as e:
        return error_response(f"Failed to delete student: {str(e)}", 500)

# 6. 이름으로 학생 검색 (GET /students/search?name=<name>)
@app.route('/students/search', methods=['GET'])
def search_students():
    try:
        name = request.args.get('name')
        if not name:
            return error_response("Please provide a name to search")
        
        result = supabase.table('students').select('*').ilike('name', f'%{name}%').execute()
        students = result.data
        
        return success_response(students, f"Search for '{name}' completed")
        
    except Exception as e:
        return error_response(f"Failed to search students: {str(e)}", 500)

# 헬스 체크 엔드포인트
@app.route('/health', methods=['GET'])
def health_check():
    return success_response({"status": "healthy"}, "API server is running normally")

# 루트 엔드포인트
@app.route('/', methods=['GET'])
def root():
    return success_response({
        "endpoints": {
            "GET /students": "Get all students",
            "GET /students/<id>": "Get specific student",
            "POST /students": "Create new student",
            "PUT /students/<id>": "Update student information",
            "DELETE /students/<id>": "Delete student",
            "GET /students/search?name=<name>": "Search students by name",
            "GET /health": "Health check"
        }
    }, "Flask REST API Server")

if __name__ == '__main__':
    # 환경 설정 확인
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Warning: Supabase configuration required!")
        print("1. Create .env file and add:")
        print("   SUPABASE_URL=your-actual-supabase-url")
        print("   SUPABASE_KEY=your-actual-supabase-anon-key")
    
    print("Starting Flask REST API server...")
    print("Available endpoints:")
    print("- GET    /students          : Get all students")
    print("- GET    /students/<id>     : Get specific student")  
    print("- POST   /students          : Create new student")
    print("- PUT    /students/<id>     : Update student information")
    print("- DELETE /students/<id>     : Delete student")
    print("- GET    /students/search   : Search students by name")
    print("- GET    /health            : Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)