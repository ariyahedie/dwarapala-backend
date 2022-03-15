from email.policy import default
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ariyahedie290500@localhost/dwarapala'
db = SQLAlchemy(app)
# CORS(app, resources={"/*": {"origins": ["http://localhost:3000"]}})
CORS(app)
# app.config['supportsCredentials'] = True
# app.config['allowedOrigins'] = ['*']
# app.config['allowedOriginsPatterns'] = []
# app.config['allowedHeaders'] = ['*']
# app.config['allowedMethods'] = ['*']
# app.config['exposedHeaders'] = []
# app.config['maxAge'] = 0

class Company(db.Model):
  company_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  usertype_id = db.Column(db.Integer, db.ForeignKey('usertype.usertype_id'))
  company_name = db.Column(db.String(50), nullable=False)
  company_email = db.Column(db.String(50), nullable=False)
  company_password = db.Column(db.String(50), nullable=False)
  company_created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
  company_account_status = db.Column(db.String(50), nullable=False, default='pending')

  position = db.relationship('Position', backref='company')
  department = db.relationship('Department', backref='company')
  member = db.relationship('Member', backref='company')

  def __init__(self, usertype_id, company_name, company_email, company_password):
    self.usertype_id = usertype_id
    self.company_name = company_name
    self.company_email = company_email
    self.company_password = company_password

  def __repr__(self):
    return f"Company: {self.company_name}"

class Position(db.Model):
  position_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  position_name = db.Column(db.String(50), nullable=False)
  company_id = db.Column(UUID(as_uuid=True), db.ForeignKey('company.company_id'))

  member = db.relationship('Member', backref='position')

  def __init__(self, position_name, company_id):
    self.position_name = position_name
    self.company_id = company_id

  def __repr__(self):
    return f"Position: {self.position_name}"

class Department(db.Model):
  department_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  department_name = db.Column(db.String(50), nullable=False)
  company_id = db.Column(UUID(as_uuid=True), db.ForeignKey('company.company_id'))

  member = db.relationship('Member', backref='department')

  def __init__(self, department_name, company_id):
    self.department_name = department_name
    self.company_id = company_id

  def __repr__(self):
    return f"Department: {self.department_name}"

class Usertype(db.Model):
  usertype_id = db.Column(db.Integer, primary_key=True)
  usertype_name = db.Column(db.String(50), nullable=False)

  member = db.relationship('Member', backref='usertype')
  superadmin = db.relationship('Superadmin', backref='usertype')
  company = db.relationship('Company', backref='usertype')

  def __init__(self, usertype_name):
    self.usertype_name = usertype_name

  def __repr__(self):
    return f"Usertype: {self.usertype_name}"

class Member(db.Model):
  member_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  company_id = db.Column(UUID(as_uuid=True), db.ForeignKey('company.company_id'))
  position_id = db.Column(UUID(as_uuid=True), db.ForeignKey('position.position_id'))
  usertype_id = db.Column(db.Integer, db.ForeignKey('usertype.usertype_id'))
  department_id = db.Column(UUID(as_uuid=True), db.ForeignKey('department.department_id'))
  member_name = db.Column(db.String(50), nullable=False)
  member_email = db.Column(db.String(50), nullable=False)
  member_password = db.Column(db.String(50), nullable=False)
  member_images = db.Column(db.String(50), nullable=True, default='')
  member_created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

  def __init__(self, member_name, company_id, position_id, usertype_id, department_id, member_email, member_password, member_images):
    self.member_name = member_name
    self.company_id = company_id
    self.position_id = position_id
    self.usertype_id = usertype_id
    self.department_id = department_id
    self.member_email = member_email
    self.member_password = member_password
    self.member_images = member_images

  def __repr__(self):
    return f"Member: {self.member_name}"

class Superadmin(db.Model):
  superadmin_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  usertype_id = db.Column(db.Integer, db.ForeignKey('usertype.usertype_id'))
  superadmin_name = db.Column(db.String(50), nullable=False)
  superadmin_email = db.Column(db.String(50), nullable=False)
  superadmin_password = db.Column(db.String(50), nullable=False)

  def __init__(self, usertype_id, superadmin_name, superadmin_email, superadmin_password):
    self.usertype_id = usertype_id
    self.superadmin_name = superadmin_name
    self.superadmin_email = superadmin_email
    self.superadmin_password = superadmin_password

  def __repr__(self):
    return f"Superadmin: {self.superadmin_name}"

class Log(db.Model):
  log_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  member_id = db.Column(UUID(as_uuid=True), db.ForeignKey('member.member_id'))
  log_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

  def __init__(self, member_id, log_time):
    self.member_id = member_id
    self.log_time = log_time

  def __repr__(self):
    return f"Log Time: {self.log_time}, Member ID: {self.member_id}"

class Image(db.Model):
  image_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  member_id = db.Column(UUID(as_uuid=True), db.ForeignKey('member.member_id'))
  image_name = db.Column(db.String(50), nullable=False)

  def __init__(self, member_id, image_name):
    self.member_id = member_id
    self.image_name = image_name

  def __repr__(self):
    return f"Image Name: {self.image_name}, Member ID: {self.member_id}"

def format_company(company):
  return {
    "id": company.company_id,
    "name": company.company_name,
    "usertype": company.usertype_id
  }

def format_usertype(usertype):
  return {
    "name": usertype.usertype_name
  }

def format_department(department):
  return {
    "department": department.department_name,
    "company": department.company_id
  }

def format_position(position):
  return {
    "position": position.position_name,
    "company": position.company_id
  }

@app.route('/')
def index():
  return ''

# create an company
@app.route('/company', methods=['POST'])
def create_company():
  name = request.json['name']
  email = request.json['email']
  password = request.json['password']
  company = Company(1, name, email, password)
  db.session.add(company)
  db.session.commit()
  return format_company(company)

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

# # edit an event
# @app.route('/event/<id>', methods=['PUT'])
# def update_event(id):
#   event = Event.query.filter_by(id=id)
#   description = request.json['description']
#   event.update(dict(description=description, created_at=datetime.utcnow()))
#   db.session.commit()
#   return {
#     'event': format_event(event.one())
#   }


if __name__ == '__main__':
  app.run(debug=True)