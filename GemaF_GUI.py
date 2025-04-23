# Ramiro Isa-Jara, ramiro.isaj@gmail.com
# GEMA -> Gabor filter Experiments with Morphology operations in Applications of cells segmentation
# Interface GEMA_F - CELL Analysis in Bright and Fluorescent Fields
import PySimpleGUI as sg
import numpy as np
import pandas as pd
import GemaF_Def as Gd
import GemaF_B as Gb
import GemaF_F as Gf
from datetime import datetime
import time

# -------------------------------
# Adjust size screen
# -------------------------------
Screen_size = 10
# -------------------------------
sg.theme('LightGrey1')
m1, n1 = 450, 400
img = np.ones((m1, n1, 1), np.uint8)*255

l_res = ['100x', '90x', '60x', '40x', '20x', '10x', '4x']
l_cont = ['12.5', '25.0']
layout1 = [[sg.Radio('Windows', "RADIO1", enable_events=True, default=True, key='_SYS_')],
           [sg.Radio('Linux', "RADIO1", enable_events=True, key='_LIN_')], [sg.Text('')]]

layout2 = [[sg.Checkbox('*.tif', default=True, key="_IN3_")],
           [sg.Checkbox('*.jpg', default=False, key="_IN1_")],
           [sg.Checkbox('*.png', default=False, key="_IN2_")],]


layout3 = [[sg.Text('', size=(5, 1)),
            sg.Radio('Bright field', "RADIO2", default=True, key='_BFR_', font=('Arial', 9, 'bold')),
            sg.Text('', size=(4, 1)),
           sg.Radio('Fluorescent field', "RADIO2", font=('Arial', 9, 'bold'))],
           [sg.Text('Image resolution:', size=(12, 1)), sg.Combo(l_res, size=(5, 1), default_value='10x', key='_RES_'),
            sg.Text('', size=(1, 1)),
            sg.Text('Contrast level:', size=(10, 1)), sg.Combo(l_cont, size=(5, 1), default_value='12.5', key='_COT_'),
            sg.Text('', size=(1, 1)),],
           [sg.Text('BF-sections:', size=(12, 1)), sg.InputText('20', key='_BFS_', size=(7, 1)),
            sg.Text('', size=(1, 1)),
            sg.Text('FF-sections:', size=(10, 1)), sg.InputText('16', key='_FFS_', size=(6, 1))],
           [sg.Checkbox('Save Color Images', default=True, key='_SIC_'), sg.Text('', size=(4, 1)),
            sg.Checkbox('Save Binary Images', default=False, key='_SIB_')],]

layout4 = [[sg.Text('Source : ', size=(10, 1), key='_F_', visible=True),
            sg.InputText(size=(62, 1), key='_ORI_', visible=True), sg.FolderBrowse(visible=True, key='_FOL_'),
            sg.Text('Source : ', size=(10, 1), key='_FI_', visible=False), sg.InputText(size=(62, 1), key='_ORF_', visible=False),
            sg.FileBrowse(visible=False, key='_FIL_')],
           [sg.Text('Destiny: ', size=(10, 1)), sg.InputText(size=(62, 1), key='_DES_'), sg.FolderBrowse()]]

layout5 = [[sg.T("", size=(30, 1)), sg.Text('NO PROCESS', size=(42, 1), key='_MES_', text_color='DarkRed')]]

layout6 = [[sg.Text('Current time: ', size=(10, 1)), sg.Text('', size=(12, 1), key='_TAC_'), sg.T("", size=(2, 1)),
            sg.Text('Start time:', size=(10, 1)), sg.Text('-- : -- : --', size=(11, 1), key='_TIN_', text_color='blue'),
            sg.Text('Finish time: ', size=(9, 1)), sg.Text('-- : -- : --', size=(9, 1), key='_TFI_', text_color='red')],
           [sg.Text('Experiment:', size=(11, 1)), sg.InputText('', key='_NEX_', size=(25, 1)),
            sg.Text('', size=(2, 1)),
            sg.Text('Image name:', size=(10, 1)), sg.InputText('', key='_NIM_', size=(25, 1)),],
           [sg.Text('Current image: ', size=(11, 1)), sg.InputText('', key='_CUR_', size=(10, 1)),
            sg.Text('', size=(15, 1)),
           sg.Text('Total images: ', size=(10, 1)), sg.InputText('', key='_CIM_', size=(10, 1))],
           ]

layout7 = [[sg.Text('', size=(4, 1)),
            sg.Text('Nr. of Regions: ', size=(12, 1)), sg.InputText('', key='_SPH_', size=(10, 1)),
            sg.Text('', size=(14, 1)),
            sg.Text('Time used: ', size=(10, 1)), sg.InputText('', key='_TUS_', size=(8, 1)),
            sg.Text('...', size=(3, 1), key='_IDE_'), sg.Text('', size=(3, 1))],
           [sg.Text('', size=(4, 1)),
            sg.Text('Image area: ', size=(12, 1)), sg.InputText('', key='_TAR_', size=(10, 1)),
            sg.Text('um2', size=(4, 1)),],
           [sg.Text('', size=(4, 1)),
            sg.Text('Detected area: ', size=(12, 1)), sg.InputText('', key='_DAR_', size=(10, 1)),
            sg.Text('um2', size=(4, 1)),  sg.Text('', size=(8, 1)),
            sg.Text('Percentage: ', size=(10, 1)), sg.InputText('', key='_PAR_', size=(8, 1)),
            sg.Text('%', size=(3, 1)),sg.Text('', size=(3, 1))]
           ]


v_image = [sg.Image(filename='', key="_IMA_")]
# columns
col_1 = [[sg.Frame('', [v_image])]]
col_2 = [[sg.Frame('Operative System: ', layout1, title_color='Blue'),
          sg.Frame('Type image: ', layout2, title_color='Blue'), sg.Frame('Settings: ', layout3, title_color='Blue')],
         [sg.Frame('Directories: ', layout4, title_color='Blue', key='_DIR_')],
         [sg.Text(" ", size=(25, 1)), sg.Button('Start', size=(8, 1)),
          sg.Button('Pause', size=(8, 1)), sg.Button('Finish', size=(8, 1))],
         [sg.Frame('', layout5)], [sg.Frame('', layout6)],
         [sg.Frame('Results: ', layout7, title_color='Blue'),],]

layout = [[sg.Column(col_1), sg.Column(col_2)]]

# Create the Window
window = sg.Window('GEMA-F Analysis Interface', layout, font="Helvetica "+str(Screen_size), finalize=True)
window['_IMA_'].update(data=Gd.bytes_(img, m1, n1))
# ---------------------------------------------------------------------
time_, id_image, i = 0, 0, 0
start_f, start_b, save_color, save_bin, finish_, pause_ = False, False, True, False, False, False
sections, name, image, ini_time, ini_time_, path_des, type_i, path_ori = None, None, None, None, None, None, None, None
saveIm, filenames, id_sys, name_file, contrast = None, [], 0, None, 0
results = pd.DataFrame(columns=['Image', 'Regions', 'Percentage Area', 'Image Area (um2)', 'Detected Area (um2)',
                                'Time (sec)'])
# ------------------------------------------------------------------------
gemaB = Gb.GemaFBright(window)
gemaB.build_filters()
# ------------------------------------------------------------------------
gemaF = Gf.GemaFFluorescent(window)
gemaF.build_filters()
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read(timeout=10)
    window.Refresh()

    if event is None or event == sg.WIN_CLOSED:
        break

    now = datetime.now()
    now_time = now.strftime("%H : %M : %S")
    window['_TAC_'].update(now_time)

    if event == 'Finish' or finish_:
        print('FINISH PROCESS')
        now_time = now.strftime("%H : %M : %S")
        window['_TFI_'].update(now_time)
        window['_MES_'].update('Process is completed')
        if start_b:
            Gd.save_csv_file(results, path_des, 'BF')
        if start_f:
            Gd.save_csv_file(results, path_des, 'FF')
        start_b, start_f, finish_, i = False, False, False, 0
        results = pd.DataFrame(columns=['Image', 'Regions', 'Percentage Area', 'Image Area (um2)',
                                        'Detected Area (um2)', 'Time (sec)'])
        gemaB = Gb.GemaFBright(window)
        gemaB.build_filters()
        gemaF = Gf.GemaFFluorescent(window)
        gemaF.build_filters()

    if event == 'Pause':
        if not pause_:
            start_ = False
            pause_ = True
            window['_MES_'].update('  Press PAUSE to resume ...')
        else:
            start_ = True
            pause_ = False

    if values['_IN1_']:
        type_i = ".jpg"
        window['_IN2_'].update(False)
        window['_IN3_'].update(False)
        window['_F_'].update(visible=True)
        window['_ORI_'].update(visible=True)
        window['_FOL_'].update(visible=True)
        window['_FIL_'].update(visible=False)
        window['_ORF_'].update(visible=False)
        window['_FI_'].update(visible=False)

    if values['_IN2_']:
        type_i = ".png"
        window['_IN1_'].update(False)
        window['_IN3_'].update(False)
        window['_F_'].update(visible=True)
        window['_ORI_'].update(visible=True)
        window['_FOL_'].update(visible=True)
        window['_FIL_'].update(visible=False)
        window['_ORF_'].update(visible=False)
        window['_FI_'].update(visible=False)

    if values['_IN3_']:
        type_i = ".tif"
        window['_IN1_'].update(False)
        window['_IN2_'].update(False)
        window['_F_'].update(visible=True)
        window['_ORI_'].update(visible=True)
        window['_FOL_'].update(visible=True)
        window['_FIL_'].update(visible=False)
        window['_ORF_'].update(visible=False)
        window['_FI_'].update(visible=False)

    if event == 'Start':
        print('START ANALYSIS')
        now_time = now.strftime("%H : %M : %S")
        window['_TIN_'].update(now_time)
        if values['_SYS_']:
            path_ori = Gd.update_dir(values['_ORI_']) + "\\"
            path_ori = r'{}'.format(path_ori)
            path_des = Gd.update_dir(values['_DES_']) + "\\"
            path_des = r'{}'.format(path_des)
            id_sys = 0
        else:
            path_ori = values['_ORI_'] + '/'
            path_des = values['_DES_'] + '/'
            id_sys = 1
        # -------------------------------------------------------------------
        window['_IDE_'].update('sec')
        # -------------------------------------------------------------------
        if len(path_ori) > 1 and len(path_des) > 1 and start_b is False and start_f is False:
            save_color = values['_SIC_']
            save_bin = values['_SIB_']
            if values['_BFR_']:
                start_b, start_f = True, False
                sections = int(values['_BFS_'])
            else:
                start_f, start_b = True, False
                sections = int(values['_FFS_'])
                contrast = float(values['_COT_'])
            ini_time = datetime.now()
        elif len(path_ori) > 1 and len(path_des) > 1 and (start_b or start_f):
            sg.Popup('Warning', ['Analysis is running...'])
        else:
            sg.Popup('Error', ['Information or process is incorrect'])

        print(start_f)

    if start_b:
        filenames, image_, experiment, filename, total_i = Gd.load_image_i(path_ori, i, type_i, filenames, id_sys)
        window['_CIM_'].update(total_i)

        if len(image_) == 0 and total_i == 0:
            finish_ = True
            sg.Popup('Error', ['No images in directory. '])
        elif i == total_i:
            finish_ = True
            continue
        else:
            window['_CUR_'].update(i + 1)
            window['_CIM_'].update(total_i)
            window['_NIM_'].update(filename)
            window['_NEX_'].update(experiment)
            window['_IMA_'].update(data=Gd.bytes_(image_, m1, n1))
            window['_MES_'].update(' ... IMAGE PROCESSING .... ')
            print('|-------------------------------------------------------|')
            print('Processing image: ... ' + str(i + 1) + ' of ' + str(total_i))
            image_out, binary_out, results = gemaB.main(image_, filename, sections, results)
            window['_IMA_'].update(data=Gd.bytes_(image_out, m1, n1))

            if save_color:
                Gd.save_image_color(image_out, path_des, filename)

            if save_bin:
                Gd.save_image_binary(binary_out, path_des, filename)

            i += 1
            time.sleep(0.10)

    if start_f:
        filenames, image_, experiment, filename, total_i = Gd.load_image_i(path_ori, i, type_i, filenames, id_sys)
        window['_CIM_'].update(total_i)

        if len(image_) == 0 and total_i == 0:
            finish_ = True
            sg.Popup('Error', ['No images in directory. '])
        elif i == total_i:
            finish_ = True
            continue
        else:
            window['_CUR_'].update(i + 1)
            window['_CIM_'].update(total_i)
            window['_NIM_'].update(filename)
            window['_NEX_'].update(experiment)
            window['_IMA_'].update(data=Gd.bytes_(image_, m1, n1))
            window['_MES_'].update(' ... IMAGE PROCESSING .... ')
            print('|-------------------------------------------------------|')
            print('Processing image: ... ' + str(i + 1) + ' of ' + str(total_i))
            image_out, binary_out, results = gemaF.main(i, image_, filename, sections, contrast, results)
            window['_IMA_'].update(data=Gd.bytes_(image_out, m1, n1))

            if save_color:
                Gd.save_image_color(image_out, path_des, filename)

            if save_bin:
                Gd.save_image_binary(binary_out, path_des, filename)

            i += 1
            time.sleep(0.10)

print('CLOSE WINDOW')
window.close()
