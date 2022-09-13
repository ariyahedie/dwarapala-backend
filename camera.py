import cv2
from PIL import Image
import requests
from face_detector import Detector
from face_recognizer import Recognizer
import numpy as np

class VideoCamera(object):
  def __init__(self):
    self.video = cv2.VideoCapture(0)
    self.detector = Detector()
    self.recognizer = Recognizer()
    self.frame_count = 0
    self.start_point = 0
    self.end_point = 0
    self.name = ''
    self.status = 0
  
  def __del__(self):
    self.frame_count = 0
    self.video.release()
  
  def get_frame(self, model, ann_model, out_encoder):
    access = ''
    ret, frame = self.video.read()
    frame = cv2.flip(frame, 1)
    if ret:
      self.frame_count = self.frame_count + 1
    # if ret:
    frame_to_be_processed = cv2.resize(frame,(320,320), fx=0, fy=0, interpolation = cv2.INTER_CUBIC)
    im_pil = Image.fromarray(frame_to_be_processed)
    im_cv = np.array(im_pil)

    if self.status != 0:
      access = 'access granted'
      self.status = self.status - 1
      print(self.status)
      face_arr, box = self.detector.detect_face(im_cv)
      face_arr = None
    else:
      face_arr, box = self.detector.detect_face(im_cv)

    if face_arr is not None:
      # convert face to an embedding
      embedding = self.recognizer.get_embedding(model, face_arr)

      # prediction for the face
      samples = np.expand_dims(embedding, axis=0)
      yhat_class = ann_model.predict(samples)
      yhat_prob = np.argmax(yhat_class, axis=-1)
      class_probability = yhat_class[0, yhat_prob[0]] * 100
      predict_names = out_encoder.inverse_transform(yhat_prob)
      
      if class_probability < 54:
        name = 'UNKNOWN'
        print('UNKNOWN: (%.3f)' % (class_probability))
        img_drawn = self.detector.draw_boxes(im_cv, box, 'UNKNOWN')
      else:
        name = predict_names[0]
        print('Predicted: %s (%.3f)' % (predict_names[0], class_probability))

      if name == 'UNKNOWN':
        self.name = name
        self.start_point = self.frame_count
        self.end_point = self.frame_count
        color = (0,0,255)
      elif name == self.name:
        self.end_point = self.frame_count
        if (self.end_point - self.start_point) > 6:
          self.status = 6
          access = 'access granted'
          response = requests.post("http://localhost:5000/log", json={'member_email': name})
          print('access granted')
          print(response.text)
        else:
          self.status = 0
        color = (0,255,0)
      else:
        self.name = name
        self.start_point = self.frame_count
        self.end_point = self.frame_count
        color = (0,255,0)
      img_drawn = self.detector.draw_boxes(im_cv, box, name, color)
      img_drawn = self.draw_access_granted(img_drawn, access)
      ret, jpeg = cv2.imencode('.jpg', img_drawn)
    else:
      self.name = ''
      self.start_point = self.frame_count
      self.end_point = self.frame_count
      frame_to_be_processed = self.draw_access_granted(frame_to_be_processed, access)
      ret, jpeg = cv2.imencode('.jpg', frame_to_be_processed)
    
    print(str(self.end_point - self.start_point)+' frames - '+self.name)
    return jpeg.tobytes()

  def draw_access_granted(self, frame, access=''):
    img = cv2.putText(frame, access, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    return img

  def get_frame_face_detection_only(self):
    ret, frame = self.video.read()
    # if ret:
    frame_to_be_processed = cv2.resize(frame,(320,320), fx=0, fy=0, interpolation = cv2.INTER_CUBIC)
    im_pil = Image.fromarray(frame_to_be_processed)
    face_arr, box = self.detector.detect_face(im_pil)

    if face_arr is not None:
      img_drawn = self.detector.draw_boxes(im_pil, box, 'face detected')
      ret, jpeg = cv2.imencode('.jpg', img_drawn)
    else:
      ret, jpeg = cv2.imencode('.jpg', frame_to_be_processed)
    return jpeg.tobytes()