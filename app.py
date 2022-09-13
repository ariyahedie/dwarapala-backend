from flask import Flask, jsonify, request, session, Response
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
from datetime import datetime
from config import ApplicationConfig, UsertypeId
from models import *
from format_models import *

import os
import numpy as np
from face_recognizer import Recognizer
from camera import VideoCamera
from PIL import Image
import base64
import io
import time
from face_recognizer import Recognizer
import cv2
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt = Bcrypt(app)
server_session = Session(app)
db.init_app(app)

with app.app_context():
  db.create_all()

CORS(app, supports_credentials=True)

def gen_face_det(camera):
  while True:
    frame = camera.get_frame_face_detection_only()
    yield (b'--frame\r\n'
      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def gen(camera, company_id):
  recognizer = Recognizer()
  # get keras model
  model = recognizer.load_model('FaceNet_Keras_converted.h5')
  # load the model from disk
  ann_model = tf.keras.models.load_model('member_images_dataset/'+company_id+'/ann_model.h5')
  out_encoder = LabelEncoder()
  out_encoder.classes_ = np.load('member_images_dataset/'+company_id+'/classes.npy')
  
  while True:
    frame = camera.get_frame(model, ann_model, out_encoder)
    yield (b'--frame\r\n'
      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def view_image(img_dir):
  im = cv2.imread(img_dir)
  img_str = cv2.imencode('.jpg', im)[1].tostring()
  yield (b'--frame\r\n'
      b'Content-Type: image/jpeg\r\n\r\n' + img_str + b'\r\n\r\n')

@app.route('/video_feed/<company_id>')
def video_feed(company_id):
  return Response(gen(VideoCamera(), company_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/image_view/<member_id>')
def image_view(member_id):
  member = Member.query.filter_by(member_id=member_id).first()
  for (_, _, file) in os.walk(member.member_images):
    for f in file:
      if '.jpg' in f:
        path = member.member_images +'/'+ f
  return Response(view_image(path), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_train_images/')
def capture_train_images():
  return Response(gen_face_det(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
  return ''
 
@app.route('/upload_image', methods=['POST'])
def upload_image():
  data = request.json['data']
  company_id = request.json['company_id']
  email = request.json['email']

  directory = './member_images_dataset/'+(str(company_id))+'/'+(str(email))

  # if data:
  if not os.path.exists(directory):
    os.mkdir(directory)
  try:
    time.sleep(1)
    # print(result)
    b = bytes(data, 'utf-8')
    image = b[b.find(b'/9'):]
    im = Image.open(io.BytesIO(base64.b64decode(image)))
    file_count = len([entry for entry in os.listdir(directory) if os.path.isfile(os.path.join(directory, entry))])
    im.save(directory+'/'+email+'('+str(file_count+1)+').jpg')
  except:
    pass
  return 'done'

@app.route('/update_embeddings/<company_id>', methods=['GET'])
def update_embeddings(company_id):
  recog = Recognizer()
  recog.save_to_db(company_id)
  recog.save_embeddings(company_id)
  recog.train_classification_model(company_id)
  return 'updated'

# do pictures of this user exist
@app.route('/pic_count/<user_id>', methods=['GET'])
def pic_count(user_id):
  member = Member.query.filter_by(member_id=user_id).first()
  path = './member_images_dataset/'+(str(member.company_id))+'/'+(str(member.member_email))

  if not os.path.exists(path):
    return {
      'count': 0
    }
  else:
    # create empty List
    listOfFiles = list()
    for (directory, subdirectories, file) in os.walk(path):
      for f in file:
        if '.jpg' in f:
          listOfFiles.append(os.path.join(directory,f))
    return {
      'count': len(listOfFiles)
    }

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
      "password": company.company_password,
      "status": company.company_account_status
    })

  member = Member.query.filter_by(member_id=user_id).first()
  if member is not None:
    return jsonify({
      "id": member.member_id,
      "name": member.member_name,
      "company": member.company_id,
      "position": member.position_id,
      "usertype": member.usertype_id,
      "department": member.department_id,
      "email": member.member_email,
      "images": member.member_images,
      "created_at": member.member_created_at,
      "password": member.member_password
    })

  superadmin = Superadmin.query.filter_by(superadmin_id=user_id).first()
  if superadmin is not None:
    return jsonify({
      "id": superadmin.superadmin_id,
      "name": superadmin.superadmin_name,
      "usertype": superadmin.usertype_id,
      "email": superadmin.superadmin_email,
      "password": superadmin.superadmin_password
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

# update a company name
@app.route('/update-company-name/<company_id>', methods=['PUT'])
def update_company_name(company_id):
  company = Company.query.filter_by(company_id=company_id)
  name = request.json['name']

  if company is None:
    return

  company.update(dict(company_name=name, company_created_at=datetime.utcnow()))
  db.session.commit()
  return {
    'company': format_company(company.one())
  }

# update a company password
@app.route('/update-company-password/<company_id>', methods=['PUT'])
def update_company_password(company_id):
  company = Company.query.filter_by(company_id=company_id)

  password = request.json['password']
  newPassword = request.json['newPassword']
  hashed_new_password = bcrypt.generate_password_hash(newPassword).decode('utf8')
  
  if not bcrypt.check_password_hash(company[0].company_password, password):
    return jsonify({"error": "Unauthorized"}), 401

  company.update(dict(company_password=hashed_new_password, company_created_at=datetime.utcnow()))
  db.session.commit()
  return {
    'company': format_company(company.one())
  }

# update a superadmin name
@app.route('/update-superadmin-name/<superadmin_id>', methods=['PUT'])
def update_superadmin_name(superadmin_id):
  superadmin = Superadmin.query.filter_by(superadmin_id=superadmin_id)
  name = request.json['name']

  if superadmin is None:
    return

  superadmin.update(dict(superadmin_name=name))
  db.session.commit()
  return {
    'superadmin': format_superadmin(superadmin.one())
  }

# update a superadmin password
@app.route('/update-superadmin-password/<superadmin_id>', methods=['PUT'])
def update_superadmin_password(superadmin_id):
  superadmin = Superadmin.query.filter_by(superadmin_id=superadmin_id)

  password = request.json['password']
  newPassword = request.json['newPassword']
  hashed_new_password = bcrypt.generate_password_hash(newPassword).decode('utf8')
  
  if not bcrypt.check_password_hash(superadmin[0].superadmin_password, password):
    return jsonify({"error": "Unauthorized"}), 401

  superadmin.update(dict(superadmin_password=hashed_new_password))
  db.session.commit()
  return {
    'superadmin': format_superadmin(superadmin.one())
  }

# update a admin name
@app.route('/update-admin-name/<admin_id>', methods=['PUT'])
def update_admin_name(admin_id):
  admin = Member.query.filter_by(member_id=admin_id)
  name = request.json['name']

  if admin is None:
    return

  admin.update(dict(member_name=name))
  db.session.commit()
  return {
    'admin': format_member(admin.one())
  }

# update a admin password
@app.route('/update-admin-password/<admin_id>', methods=['PUT'])
def update_admin_password(admin_id):
  admin = Member.query.filter_by(member_id=admin_id)

  password = request.json['password']
  newPassword = request.json['newPassword']
  hashed_new_password = bcrypt.generate_password_hash(newPassword).decode('utf8')
  
  if not bcrypt.check_password_hash(admin[0].member_password, password):
    return jsonify({"error": "Unauthorized"}), 401

  admin.update(dict(member_password=hashed_new_password))
  db.session.commit()
  return {
    'admin': format_member(admin.one())
  }

# update admin department
@app.route('/update-admin-department/<admin_id>', methods=['PUT'])
def update_admin_department(admin_id):
  admin = Member.query.filter_by(member_id=admin_id)

  department_id = request.json['department_id']

  admin.update(dict(department_id=department_id))
  db.session.commit()
  return {
    'admin': format_member(admin.one())
  }

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

# fetch logs
@app.route('/logs', methods=['GET'])
def fetch_log():
  logs = Log.query.order_by(Log.log_time.desc()).all()
  log_list = []
  for log in logs:
    log_list.append(format_log(log))
  return {
    'logs': log_list
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

# create a log
@app.route('/log', methods=['POST'])
def create_log():
  member_email = request.json['member_email']
  member = Member.query.filter_by(member_email=member_email).first()
  log = Log(member.member_id)
  db.session.add(log)
  db.session.commit()
  return format_log(log)

# create a position
@app.route('/position', methods=['POST'])
def create_position():
  position_name = request.json['position']
  company_id = request.json['company_id']

  already_existed = Position.query.filter_by(position_name=position_name, company_id=company_id).first() is not None
  if already_existed:
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
  # company_name = request.json['company_name']
  position_id = request.json['position_id']
  department_id = request.json['department_id']
  name = request.json['name']
  email = request.json['email']
  password = request.json['password']
  hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
  member_images = 'member_images_dataset/' + company_id + '/' + email

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

# get a member
@app.route('/member_by_id/<member_id>', methods=['GET'])
def get_member(member_id):
  member = Member.query.filter_by(member_id=member_id).one()
  formatted_member = format_member(member)
  return {
    'member': formatted_member
  }

# get a position by position_id
@app.route('/position-by-position/<position_id>', methods=['GET'])
def get_position(position_id):
  position = Position.query.filter_by(position_id=position_id).one()
  formatted_position = format_position(position)
  return {
    'position': formatted_position
  }

# get a department by department_id
@app.route('/department-by-department/<department_id>', methods=['GET'])
def get_department(department_id):
  department = Department.query.filter_by(department_id=department_id).one()
  return {
    'department': format_department(department)
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

if __name__ == '__main__':
  app.run(debug=True)