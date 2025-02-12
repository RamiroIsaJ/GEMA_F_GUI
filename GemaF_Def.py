# Ramiro Isa-Jara, ramiro.isaj@gmail.com
# Interface GEMA_F - CELL Analysis in Bright and Fluorescent Fields
import numpy as np
import cv2
import glob
import os
import matplotlib.pyplot as plt


def load_image_i(orig, i, type_, filenames, id_sys):
    symbol = '\\' if id_sys == 0 else '/'
    if len(filenames) == 0:
        filenames = [img for img in glob.glob(orig + '*' + type_)]
        filenames.sort()
    if i < len(filenames):
        name = filenames[i]
        parts = name.split(symbol)
        name_exp, name_ima = parts[len(parts)-2], parts[len(parts)-1]
        # read image
        image_ = cv2.imread(name)
    else:
        image_, name_ima, name_exp = [], [], []
    return filenames, image_, name_exp, name_ima, len(filenames)


def update_dir(path):
    path_s = path.split('/')
    cad, path_f = len(path_s), path_s[0]
    for p in range(1, cad):
        path_f += '\\' + path_s[p]
    return path_f


def bytes_(img, m, n):
    ima = cv2.resize(img, (m, n))
    return cv2.imencode('.png', ima)[1].tobytes()


def save_image_color(ima_out_, path_des_, name_ima):
    root_ima = os.path.join(path_des_, name_ima+'.jpg')
    cv2.imwrite(str(root_ima), ima_out_)
    print('------------------------------------------')
    print('..... Color image saved successfully .....')
    print('------------------------------------------')


def save_image_binary(ima_bin_, path_des_, name_ima):
    name_cc = name_ima.split('.')[0]
    root_ima = os.path.join(path_des_, name_cc+'.jpg')
    plt.imsave(str(root_ima), ima_bin_, cmap='gray')
    print('-------------------------------------------')
    print('..... Binary image saved successfully .....')
    print('-------------------------------------------')


def save_csv_file(results_, path_des_, id_):
    root_file = os.path.join(path_des_, 'Data_results_'+str(id_)+'.csv')
    results_.to_csv(str(root_file), index=False)
    print('----------------------------------------------')
    print('..... Save data in CSV file successfully .....')
    print('----------------------------------------------')
