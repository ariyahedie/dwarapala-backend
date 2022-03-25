from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
from datetime import datetime
from config import ApplicationConfig, UsertypeId
from models import *
from format_models import *

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt = Bcrypt(app)
server_session = Session(app)
db.init_app(app)

with app.app_context():
  db.create_all()

CORS(app, supports_credentials=True)

@app.route('/')
def index():
  return ''

@app.route('/@me')
def get_current_user():
  user_id = session.get("user_id")

  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401
  
  company = Company.query.filter_by(company_id=user_id).first()
  if company is not None:
    return jsonify({
      "id": company.company_id,
      "name": company.company_name,
      "created_at": company.company_created_at,
      "usertype": company.usertype_id,
      "email": company.company_email,
      "status": company.company_account_status
    })

  member = Member.query.filter_by(member_id=user_id).first()
  if member is not None:
    return jsonify({
      "id": member.member_id,
      "company": member.company_id,
      "position": member.position_id,
      "usertype": member.usertype_id,
      "department": member.department_id,
      "email": member.member_email,
      "images": member.member_images,
      "created_at": member.member_created_at
    })

  superadmin = Superadmin.query.filter_by(superadmin_id=user_id).first()
  if superadmin is not None:
    return jsonify({
      "id": superadmin.superadmin_id,
      "name": superadmin.superadmin_name,
      "usertype": superadmin.usertype_id,
      "email": superadmin.superadmin_email
    })

# create a company
@app.route('/signup-company', methods=['POST'])
def create_company():
  name = request.json['name']
  email = request.json['email']
  password = request.json['password']

  company_exists = Company.query.filter_by(company_email=email).first() is not None
  member_exists = Member.query.filter_by(member_email=email).first() is not None
  superadmin_exists = Superadmin.query.filter_by(superadmin_email=email).first() is not None

  if company_exists or member_exists or superadmin_exists:
    return jsonify({"error": "User already exists"}), 409

  hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
  company = Company(1, name, email, hashed_password)
  db.session.add(company)
  db.session.commit()
  return format_company(company)

# login
@app.route('/login-user', methods=['POST'])
def login():
  email = request.json['email']
  password = request.json['password']

  company = Company.query.filter_by(company_email=email).first()
  if company is not None and company.company_account_status == 'confirmed':
    if not bcrypt.check_password_hash(company.company_password, password):
      return jsonify({"error": "Unauthorized"}), 401
    session["user_id"] = company.company_id
    return jsonify({
      "id": company.company_id,
      "email": company.company_email
    })
  
  member = Member.query.filter_by(member_email=email).first()
  if member is not None:
    if not bcrypt.check_password_hash(member.member_password, password):
      return jsonify({"error": "Unauthorized"}), 401
    session["user_id"] = member.member_id
    return jsonify({
      "id": member.member_id,
      "email": member.member_email
    })
  
  superadmin = Superadmin.query.filter_by(superadmin_email=email).first()
  if superadmin is not None:
    if not bcrypt.check_password_hash(superadmin.superadmin_password, password):
      return jsonify({"error": "Unauthorized"}), 401
    session["user_id"] = superadmin.superadmin_id
    return jsonify({
      "id": superadmin.superadmin_id,
      "email": superadmin.superadmin_email
    })
  
  return jsonify({"error": "Unauthorized"}), 401

@app.route('/logout-user', methods=['POST'])
def logout():
  session.pop('user_id')
  return '200'

# fetch companies
@app.route('/company', methods=['GET'])
def fetch_company():
  companies = Company.query.order_by(Company.company_created_at.desc()).all()
  company_list = []
  for company in companies:
    company_list.append(format_company(company))
  return {
    'companies': company_list
  }

# fetch members
@app.route('/member/<company_id>', methods=['GET'])
def fetch_member(company_id):
  members = Member.query.filter(Member.company_id==company_id).all()
  member_list = []
  for member in members:
    member_list.append(format_member(member))
  return {
    'members': member_list
  }

# fetch departments
@app.route('/department/<company_id>', methods=['GET'])
def fetch_department(company_id):
  departments = Department.query.filter(Department.company_id==company_id).all()
  department_list = []
  for department in departments:
    department_list.append(format_department(department))
  return {
    'departments': department_list
  }

# fetch positions
@app.route('/position/<company_id>', methods=['GET'])
def fetch_position(company_id):
  positions = Position.query.filter(Position.company_id==company_id).all()
  position_list = []
  for position in positions:
    position_list.append(format_position(position))
  return {
    'positions': position_list
  }

# edit a company status
@app.route('/company/<id>', methods=['PUT'])
def update_company_status(id):
  company = Company.query.filter_by(company_id=id)
  status = request.json['status']
  company.update(dict(company_account_status=status, company_created_at=datetime.utcnow()))
  db.session.commit()
  return {
    'company': format_company(company.one())
  }

# create a department
@app.route('/department', methods=['POST'])
def create_department():
  department_name = request.json['department']
  company_id = request.json['company_id']
  department = Department(department_name, company_id)
  db.session.add(department)
  db.session.commit()
  return format_department(department)

# create a position
@app.route('/position', methods=['POST'])
def create_position():
  position_name = request.json['position']
  company_id = request.json['company_id']

  name_exists = Position.query.filter_by(position_name=position_name).first() is not None
  if name_exists:
    return jsonify({"error": "Position already exists"}), 409
  
  position = Position(position_name, company_id)
  db.session.add(position)
  db.session.commit()
  return format_position(position)

# create a usertype
@app.route('/usertype', methods=['POST'])
def create_usertype():
  name = request.json['name']
  usertype = Usertype(name)
  db.session.add(usertype)
  db.session.commit()
  return format_usertype(usertype)

# create a member
@app.route('/member/<company_id>', methods=['POST'])
def create_member(company_id):
  usertype_name = request.json['usertype_name']
  company_name = request.json['company_name']
  position_id = request.json['position_id']
  department_id = request.json['department_id']
  name = request.json['name']
  email = request.json['email']
  password = request.json['password']
  hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
  member_images = 'Dwarapala/images/' + company_name + '/' + email

  if usertype_name == 'admin':
    usertype_id = UsertypeId.admin
  else:
    usertype_id = UsertypeId.member

  member = Member(name, company_id, position_id, usertype_id, department_id, email, hashed_password, member_images)
  db.session.add(member)
  db.session.commit()
  return format_member(member)

@app.route('/signup-superadmin', methods=['POST'])
def create_superadmin():
  name = request.json['name']
  email = request.json['email']
  password = request.json['password']

  company_exists = Company.query.filter_by(company_email=email).first() is not None
  member_exists = Member.query.filter_by(member_email=email).first() is not None
  superadmin_exists = Superadmin.query.filter_by(superadmin_email=email).first() is not None

  if company_exists or member_exists or superadmin_exists:
    return jsonify({"error": "User already exists"}), 409

  hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
  superadmin = Superadmin(4, name, email, hashed_password)
  db.session.add(superadmin)
  db.session.commit()
  return format_superadmin(superadmin)

# get a company
@app.route('/company/<company_id>', methods=['GET'])
def get_company(company_id):
  company = Company.query.filter_by(company_id=company_id).one()
  formatted_company = format_company(company)
  return {
    'company': formatted_company
  }

@app.route('/admin-position-exist/<company_id>', methods=['GET'])
def check_if_admin_position_exist(company_id):
  isAdminPositionExist = Position.query.filter_by(company_id=company_id, position_name='Admin').first()
  if isAdminPositionExist is not None:
    return {
      'position_id': isAdminPositionExist.position_id
    }
  return {
    'position_id': ''
  }
    

# # delete an event
# @app.route('/event/<id>', methods=['DELETE'])
# def delete_event(id):
#   event = Event.query.filter_by(id=id).one()
#   db.session.delete(event)
#   db.session.commit()
#   return f"Event (id: {id}) deleted!"

if __name__ == '__main__':
  app.run(debug=True)