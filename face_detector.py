from numpy import asarray
from mtcnn.mtcnn import MTCNN
from yolo import yolov5
import cv2

class Detector:
  def __init__(self):
    self.detector = MTCNN()

  # A function to draw bounding boxes on image
  def draw_boxes(self, img, box, name, color=(255,0,0), thickness=2):
    img_array = asarray(img)
    img_copy = img_array.copy()
    # for box in bboxes:
    x1,x2,y1,y2 = box[0]
    # if (x2-x1) >= 70:
    frame = cv2.putText(img_copy, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
    frame = cv2.rectangle(img_copy, (x1,y1), (x2,y2), color, thickness)
    return frame
  
  # detect face
  def detect_face(self, image, required_size=(160, 160)):
    # convert to RGB, if needed
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # create the detector, using default weights
    yolonet = yolov5()
    # detect faces in the image
    dets = yolonet.detect(image)

    srcimg, _, box = yolonet.postprocess(image, dets)

    if srcimg.any():
      # resize pixels to the model size
      srcimg = cv2.resize(srcimg, required_size, interpolation= cv2.INTER_LINEAR)
    else:
      # resize pixels to the model size
      srcimg = cv2.resize(image, required_size, interpolation= cv2.INTER_LINEAR)
    face_array = asarray(srcimg)
    return face_array, box