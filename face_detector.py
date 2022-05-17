from numpy import asarray
from mtcnn.mtcnn import MTCNN
from PIL import Image
import cv2

class Detector:
  def __init__(self):
    self.detector = MTCNN()

  # A function to draw bounding boxes on image
  def draw_boxes(self, img, bboxes, name, color=(0,255,0), thickness=2):
    img_array = asarray(img)
    img_copy = img_array.copy()
    for box in bboxes:
      x1,y1,x2,y2 = box
      frame = cv2.putText(img_copy, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
      frame = cv2.rectangle(img_copy, (x1,y1), (x2,y2), color, thickness)
    return frame
  
  # detect face
  def detect_face(self, image, required_size=(160, 160)):
    image = image.convert('RGB')
    pixels = asarray(image)
    # detect faces in the image
    results = self.detector.detect_faces(pixels)
    if results:
      # extract the bounding box from the first face
      x1, y1, width, height = results[0]['box']
      # bug fix
      x1, y1 = abs(x1), abs(y1)
      x2, y2 = x1 + width, y1 + height
      # extract the face
      face = pixels[y1:y2, x1:x2]
      # resize pixels to the model size
      image = Image.fromarray(face)
      image = image.resize(required_size)
      face_array = asarray(image)
      box = []
      box.append((x1, y1, x2 ,y2))
      return face_array, box
    else:
      return None, None