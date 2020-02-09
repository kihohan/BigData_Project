# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings(action='ignore') 

import os
import glob
import time
import numpy as np
from tqdm import tqdm_notebook
from scipy.optimize import fmin_l_bfgs_b

import keras
from keras import backend as K
from keras.applications import vgg19
from keras.preprocessing.image import load_img, img_to_array, save_img

from google.colab import drive
drive.mount('/content/drive')

# 변환하려는 후 이미지 저장 경로
os.chdir('/content/drive/My Drive/CRUSH-IBIZA(MV) aifx/****NEW****/transfer_ize')
# os.getcwd()

# 원본 이미지 리스트
picture = glob.glob('/content/drive/My Drive/CRUSH-IBIZA(MV) aifx/****NEW****/ize/*')
picture.sort()

# 변환하려는 이미지 경로
target_image_path = picture[0]
# 스타일 이미지 경로
style_reference_image_path = '/content/drive/My Drive/CRUSH-IBIZA(MV) aifx/****NEW****/pattern/03.png'
# 생성된 사진의 차원
width, height = load_img(target_image_path).size
img_height = 1080
img_width = 1920

def preprocess_image(image_path):
    img = load_img(image_path, target_size=(img_height, img_width))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = vgg19.preprocess_input(img)
    return img

def deprocess_image(x):
    x[:, :, 0] += 103.939
    x[:, :, 1] += 116.779
    x[:, :, 2] += 123.68
    x = x[:, :, ::-1]
    x = np.clip(x, 0, 255).astype('uint8')
    return x

target_image = K.constant(preprocess_image(target_image_path))
style_reference_image = K.constant(preprocess_image(style_reference_image_path))

combination_image = K.placeholder((1, img_height, img_width, 3))
input_tensor = K.concatenate([target_image,
                              style_reference_image,
                              combination_image], axis=0)
model = vgg19.VGG19(input_tensor=input_tensor,weights='imagenet',include_top=False)
print('모델 로드 완료.')

def content_loss(base, combination):
    return K.sum(K.square(combination - base))
def gram_matrix(x):
    features = K.batch_flatten(K.permute_dimensions(x, (2, 0, 1)))
    gram = K.dot(features, K.transpose(features))
    return gram
def style_loss(style, combination):
    S = gram_matrix(style)
    C = gram_matrix(combination)
    channels = 3
    size = img_height * img_width
    return K.sum(K.square(S - C)) / (4. * (channels ** 2) * (size ** 2))
def total_variation_loss(x):
    a = K.square(
        x[:, :img_height - 1, :img_width - 1, :] - x[:, 1:, :img_width - 1, :])
    b = K.square(
        x[:, :img_height - 1, :img_width - 1, :] - x[:, :img_height - 1, 1:, :])
    return K.sum(K.pow(a + b, 1.25))

outputs_dict = dict([(layer.name, layer.output) for layer in model.layers])
content_layer = 'block5_conv2'
style_layers = ['block1_conv1','block2_conv1','block3_conv1','block4_conv1','block5_conv1']

total_variation_weight = 1e-4
style_weight = 1e5
content_weight = 1

loss = K.variable(0.)
layer_features = outputs_dict[content_layer]
target_image_features = layer_features[0, :, :, :]
combination_features = layer_features[2, :, :, :]
loss += content_weight * content_loss(target_image_features,
                                      combination_features)
for layer_name in style_layers:
    layer_features = outputs_dict[layer_name]
    style_reference_features = layer_features[1, :, :, :]
    combination_features = layer_features[2, :, :, :]
    sl = style_loss(style_reference_features, combination_features)
    loss += (style_weight / len(style_layers)) * sl
loss += total_variation_weight * total_variation_loss(combination_image)
grads = K.gradients(loss, combination_image)[0]
fetch_loss_and_grads = K.function([combination_image], [loss, grads])

class Evaluator(object):
    def __init__(self):
        self.loss_value = None
        self.grads_values = None

    def loss(self, x):
        assert self.loss_value is None
        x = x.reshape((1, img_height, img_width, 3))
        outs = fetch_loss_and_grads([x])
        loss_value = outs[0]
        grad_values = outs[1].flatten().astype('float64')
        self.loss_value = loss_value
        self.grad_values = grad_values
        return self.loss_value

    def grads(self, x):
        assert self.loss_value is not None
        grad_values = np.copy(self.grad_values)
        self.loss_value = None
        self.grad_values = None
        return grad_values

evaluator = Evaluator()

fail_list = []
tqdm_pic = tqdm_notebook(picture)
for picture_num in tqdm_pic:
    try:
      iterations = 10
      x = preprocess_image(picture_num)
      x = x.flatten()
      for i in range(iterations):
          x, min_val, info = fmin_l_bfgs_b(evaluator.loss, x,fprime=evaluator.grads, maxfun=20)
          img = x.copy().reshape((img_height, img_width, 3))
          img = deprocess_image(img)
          result_prefix = 'transfer_' + picture_num.split('/')[-1].split('.')[0]
          fname = result_prefix + '.png'
          save_img(fname, img)
    except: # gpu 할당으로 실패한 사진 파일 목록을 출력합니다.
        print (picture_num)
        fail_list.append(picture_num)

