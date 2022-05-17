import numpy as np
import os
import tensorflow as tf
from os import listdir
import os
from PIL import Image
from numpy import asarray
from mtcnn.mtcnn import MTCNN
from scipy.spatial import distance

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

class Recognizer:
  # get the face embedding for one face
  def get_embedding(self, model, face_pixels):
    # scale pixel values
    face_pixels = face_pixels.astype('float32')
    # standardize pixel values across channels (global)
    mean, std = face_pixels.mean(), face_pixels.std()
    face_pixels = (face_pixels - mean) / std
    # transform face into one sample
    samples = np.expand_dims(face_pixels, axis=0)
    # make prediction to get embedding
    yhat = model.predict(samples)
    return yhat[0]

  def load_model(self, filename):
    cwdir = os.path.curdir
    model_path = os.path.join(cwdir, 'model', filename)
    model = tf.keras.models.load_model(model_path)
    return model

  # # calculate euclidain distance between the true and predicted 
  # def calculate_distance(self, embd_real, embd_candidate):
  #   return distance.euclidean(embd_real, embd_candidate)

  # def Whoisit(self, face_embedding):
  #   distance = {}
  #   minimum_distance = None
  #   person_name = ""
  #   for name, embedding in self.database.items():
  #     distance[name] = self.calculate_distance(embedding, face_embedding)
  #     if minimum_distance == None or distance[name]<minimum_distance:
  #       minimum_distance = distance[name]
  #       person_name = name
  #   if minimum_distance>1:
  #     person_name = "UNKNOWN"
  #   return person_name, minimum_distance

  # extract a single face from a given photograph
  def extract_face(self, filename, required_size=(160, 160)):
    # load image from file
    image = Image.open(filename)
    # convert to RGB, if needed
    image = image.convert('RGB')
    # convert to array
    pixels = asarray(image)
    # create the detector, using default weights
    detector = MTCNN()
    # detect faces in the image
    results = detector.detect_faces(pixels)
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
    return face_array

  # load images and extract faces for all images in a directory
  def load_faces(self, directory):
    faces = list()
    # enumerate files
    for (_, _, file) in os.walk(directory):
      for f in file:
        if '.jpg' in f:
          # for filename in listdir(directory):
          # path
          path = directory +'/'+ f
          # get face
          face = self.extract_face(path)
          # store
          faces.append(face)
    return faces

  # load a dataset that contains one subdir for each class that in turn contains images
  def load_dataset(self, directory):
    X, y = list(), list()
    # enumerate folders, on per class
    # for subdir in listdir(directory):
      # path
      # path = directory + subdir + '/'
      # skip any files that might be in the dir
      # if not os.path.isdir(path):
      #   continue
      # load all faces in the subdirectory
    faces = self.load_faces(directory)
    # create labels
    labels = [os.path.basename(directory) for _ in range(len(faces))]
    # summarize progress
    print('>loaded %d examples for class: %s' % (len(faces), os.path.basename(directory)))
    # store
    X.extend(faces)
    y.extend(labels)
    return asarray(X), asarray(y)

  def save_to_db(self, company_id, email):
    # load train dataset
    trainX, trainy = self.load_dataset('member_images_dataset/'+company_id+'/'+email)
    print(trainX.shape, trainy.shape)

    # save arrays to one file in compressed format
    np.savez_compressed('member_images_dataset/'+company_id+'/'+email+'/member_images_dataset.npz', trainX, trainy)

  def save_embeddings(self, company_id, email):
    # load face embeddings
    data = np.load('member_images_dataset/'+company_id+'/'+email+'/member_images_dataset.npz')
    trainX, trainy = data['arr_0'], data['arr_1']

    # load model
    model = self.load_model('FaceNet_Keras_converted.h5')

    # convert each face in the train set to an embedding
    newTrainX = list()
    for face_pixels in trainX:
      embedding = self.get_embedding(model, face_pixels)
      newTrainX.append(embedding)
    newTrainX = asarray(newTrainX)
    print(newTrainX.shape)

    # save arrays to one file in compressed format
    np.savez_compressed('member_images_dataset/'+company_id+'/'+email+'/member_images_embeddings.npz', newTrainX, trainy)