import numpy as np
import os
import tensorflow as tf
from os import listdir
import os
from scipy.spatial import distance
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from yolo import yolov5
import cv2
from keras.layers import Dense
from keras.models import Sequential

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

  # calculate euclidain distance between the true and predicted 
  def calculate_distance(self, embd_real, embd_candidate):
    return distance.euclidean(embd_real, embd_candidate)

  # extract a single face from a given photograph
  def extract_face(self, filename, required_size=(160, 160)):
    # load image from file
    image = cv2.imread(filename)
    # convert to RGB, if needed
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # create the detector, using default weights
    yolonet = yolov5()
    # detect faces in the image
    dets = yolonet.detect(image)

    srcimg, _, _ = yolonet.postprocess(image, dets)

    if srcimg.any():
      # resize pixels to the model size
      srcimg = cv2.resize(srcimg, required_size, interpolation= cv2.INTER_LINEAR)
    else:
      # resize pixels to the model size
      srcimg = cv2.resize(image, required_size, interpolation= cv2.INTER_LINEAR)
    
    srcimg = cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB)
    
    face_array = np.asarray(srcimg)
    return face_array

  # load images and extract faces for all images in a directory
  def load_faces(self, directory):
    faces = list()
    # enumerate files
    for (_, _, file) in os.walk(directory):
      for f in file:
        if '.jpg' in f:
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
    for subdir in listdir(directory):
      # path
      path = directory + subdir + '/'
      # skip any files that might be in the dir
      if not os.path.isdir(path):
        continue
      # load all faces in the subdirectory
      faces = self.load_faces(path)
      # create labels
      labels = [subdir for _ in range(len(faces))]
      # summarize progress
      print('>loaded %d examples for class: %s' % (len(faces), subdir))
      # store
      X.extend(faces)
      y.extend(labels)
    return np.asarray(X), np.asarray(y)

  def save_to_db(self, company_id):
    # load train dataset
    trainX, trainy = self.load_dataset('member_images_dataset/'+company_id+'/')
    print(trainX.shape, trainy.shape)

    # save arrays to one file in compressed format
    np.savez_compressed('member_images_dataset/'+company_id+'/member_images_dataset.npz', trainX, trainy)

  def save_embeddings(self, company_id):
    # load face embeddings
    data = np.load('member_images_dataset/'+company_id+'/member_images_dataset.npz')
    trainX, trainy = data['arr_0'], data['arr_1']

    # load model
    model = self.load_model('FaceNet_Keras_converted.h5')

    # convert each face in the train set to an embedding
    newTrainX = list()
    for face_pixels in trainX:
      embedding = self.get_embedding(model, face_pixels)
      newTrainX.append(embedding)
    newTrainX = np.asarray(newTrainX)

    # save arrays to one file in compressed format
    np.savez_compressed('member_images_dataset/'+company_id+'/member_images_embeddings.npz', newTrainX, trainy)

  def train_classification_model(self, company_id):
    arr = np.load('member_images_dataset/'+company_id+'/member_images_embeddings.npz')
    trainX, trainy = arr['arr_0'], arr['arr_1']
    print(trainX[0], trainy[0])

    # normalize input vectors
    input_encoder = Normalizer(norm='l2')
    X = input_encoder.transform(trainX)

    # label encode targets
    output_encoder = LabelEncoder()
    output_encoder.fit(trainy)
    y = output_encoder.transform(trainy)
    y_categorical = tf.keras.utils.to_categorical(y, 21)

    model = Sequential()
    model.add(Dense(128, activation='relu', input_shape=(128,)))
    model.add(Dense(64, activation='relu', input_shape=(128,)))
    model.add(Dense(21, activation='softmax'))
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.summary()

    model.fit(X, y_categorical, validation_split=0.2, epochs=20, batch_size=20)

    # save the model to disk
    filename = 'member_images_dataset/'+company_id+'/ann_model.h5'
    model.save(filename, save_format='h5')