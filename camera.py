import cv2
from PIL import Image
from face_detector import Detector
from face_recognizer import Recognizer
import numpy as np

class VideoCamera(object):
  def __init__(self):
    self.video = cv2.VideoCapture(0)
    self.detector = Detector()
    self.recognizer = Recognizer()
  
  def __del__(self):
    self.video.release()
  
  def get_frame(self, model, svc_model, out_encoder):
    ret, frame = self.video.read()
    # if ret:
    frame_to_be_processed = cv2.resize(frame,(320,320), fx=0, fy=0, interpolation = cv2.INTER_CUBIC)
    im_pil = Image.fromarray(frame_to_be_processed)
    face_arr, box = self.detector.detect_face(im_pil)

    if face_arr is not None:
      # convert face to an embedding
      embedding = self.recognizer.get_embedding(model, face_arr)

      # prediction for the face
      samples = np.expand_dims(embedding, axis=0)
      yhat_class = svc_model.predict(samples)
      yhat_prob = svc_model.predict_proba(samples)

      # get name
      class_index = yhat_class[0]
      class_probability = yhat_prob[0,class_index] * 100
      predict_names = out_encoder.inverse_transform(yhat_class)
      print('Predicted: %s (%.3f)' % (predict_names[0], class_probability))
      img_drawn = self.detector.draw_boxes(im_pil, box, predict_names[0])
      ret, jpeg = cv2.imencode('.jpg', img_drawn)
    else:
      ret, jpeg = cv2.imencode('.jpg', frame_to_be_processed)
    return jpeg.tobytes()

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