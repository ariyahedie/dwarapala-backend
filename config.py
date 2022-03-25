from dotenv import load_dotenv
import os
import redis

load_dotenv()

class ApplicationConfig:
  SECRET_KEY = os.environ["SECRET_KEY"]

  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ECHO = True
  SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:ariyahedie290500@localhost/dwarapala'

  SESSION_TYPE = "redis"
  SESSION_PERMANENT = False
  SESSION_USE_SIGNER = True
  SESSION_REDIS = redis.from_url("redis://127.0.0.1:6379")

class UsertypeId:
  company = 1
  admin = 2
  member = 3
  superadmin = 4