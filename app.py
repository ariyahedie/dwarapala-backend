from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
from datetime import datetime
from config import ApplicationConfig
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
      "usertype": company.usertype_id,
      "email": company.company_email
    })

  member = Member.query.filter_by(member_id=user_id).first()
  if member is not None:
    return jsonify({
      "id": member.member_id,
      "usertype": member.usertype_id,
      "email": member.member_email
    })

  superadmin = Superadmin.query.filter_by(superadmin_id=user_id).first()
  if superadmin is not None:
    return jsonify({
      "id": superadmin.superadmin_id,
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
  if company is not None:
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
  companies = Company.query.order_by(Company.company_created_at.asc()).all()
  company_list = []
  for company in companies:
    company_list.append(format_company(company))
  return {
    'companies': company_list
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

# # get all events
# @app.route('/event', methods=['GET'])
# def get_events():
#   events = Event.query.order_by(Event.id.asc()).all()
#   event_list = []
#   for event in events:
#     event_list.append(format_event(event))
#   return {
#     'events': event_list
#   }

# # get a single event
# @app.route('/event/<id>', methods=['GET'])
# def get_single_event(id):
#   event = Event.query.filter_by(id=id).one()
#   formatted_event = format_event(event)
#   return {
#     'event': formatted_event
#   }

# # delete an event
# @app.route('/event/<id>', methods=['DELETE'])
# def delete_event(id):
#   event = Event.query.filter_by(id=id).one()
#   db.session.delete(event)
#   db.session.commit()
#   return f"Event (id: {id}) deleted!"

if __name__ == '__main__':
  app.run(debug=True)