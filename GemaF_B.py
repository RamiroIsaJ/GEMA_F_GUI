# Ramiro Isa-Jara, ramiro.isaj@gmail.com
# Interface GEMA_F - CELL Analysis in Bright and Fluorescent Fields
import cv2
import time
import numpy as np
import pandas as pd
from skimage.filters import threshold_otsu
from skimage import morphology, exposure


class GemaFBright:
    def __init__(self, window):
        self.window = window
        self.filters_ = []
        self.condition = None
        self.gabor_img_, self.final_img_, self.binary_c = None, None, None

    def preprocessing(self, img):
        image_gray_ = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clh = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(20, 20))
        clh_img = clh.apply(image_gray_)
        self.final_img_ = cv2.GaussianBlur(clh_img, (5, 5), 0)
        return self.final_img_

    def build_filters(self,):
        k_size, sigma = 21, 2.5
        for theta in np.arange(0, np.pi, np.pi / 16):
            kern = cv2.getGaborKernel((k_size, k_size), sigma, theta, 11.0, 0.90, 0, ktype=cv2.CV_32F)
            kern /= 2.5 * kern.sum()
            self.filters_.append(kern)

    def apply_gabor(self, img, filters):
        self.gabor_img_ = np.zeros_like(img)
        for kern in filters:
            np.maximum(self.gabor_img_, cv2.filter2D(img, cv2.CV_8UC3, kern), self.gabor_img_)
        return self.gabor_img_

    @staticmethod
    def sobel_ima(ima_g, limit_):
        ima_norm = ima_g / np.max(ima_g)
        enhanced_ima = 1 - np.exp(-ima_norm ** 2 / 1.5)
        ima = np.array(enhanced_ima * 255).astype(np.uint8)
        dx = cv2.Sobel(ima, cv2.CV_32F, 1, 0, ksize=3)
        dy = cv2.Sobel(ima, cv2.CV_32F, 0, 1, ksize=3)
        gx = cv2.convertScaleAbs(dx)
        gy = cv2.convertScaleAbs(dy)
        combined = cv2.addWeighted(gx, 1.5, gy, 1.5, 0)
        thresh_val_ = threshold_otsu(combined)
        sobel_ = np.array((255 * (combined > thresh_val_ - limit_))).astype(np.uint8)
        return sobel_

    @staticmethod
    def compute_percent_area(binary_ima, areas):
        area_ = np.sum(areas)
        area_total_ = np.round(((binary_ima.shape[0] / 4) * (binary_ima.shape[1] / 4)), 2)
        total_area = binary_ima.shape[0] * binary_ima.shape[1]
        roi_bin = np.where(binary_ima.ravel() == np.max(binary_ima.ravel()))[0]
        roi_area = np.round(area_/area_total_)
        return np.round((len(roi_bin) * 100) / total_area, 2), roi_area

    def verify_contour(self, contour):
        _, _, w, h = cv2.boundingRect(contour)
        self.condition = np.round(min(w, h) / max(w, h), 2)
        if self.condition > 0.6:
            return True
        else:
            return False

    def calculate_contour(self, img):
        contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        valid_contour, error_contour, area_valid = [], [], []
        for c in contours:
            area = cv2.contourArea(c)
            if area > 100:
                if self.verify_contour(c):
                    valid_contour.append(c)
                    area_valid.append(area/16)
                else:
                    error_contour.append(c)
        return valid_contour, error_contour, np.array(area_valid)

    def generate_contour(self, img, mark):
        binary = mark.copy()
        ima_sel_ = img.copy()
        ima_sel_[mark == 0] = 0
        v_contours, e_contours, area_contours = self.calculate_contour(mark)
        color1 = (0, 255, 0)
        # draw contours
        cv2.drawContours(ima_sel_, v_contours, -1, color1, 3)
        # delete binary
        # cv2.fillPoly(binary, pts=[e_contours[0]], color=(0, 0, 0))
        return ima_sel_, binary, area_contours

    def image_sections_bf(self, image_cc, binary_, sections_, min_area_):
        m, n = image_cc.shape
        m_, n_ = np.round(m / sections_), np.round(n / sections_)
        total_area = m_ * n_
        m_sections, n_sections = [0], [0]
        for i in range(sections_ - 1):
            m_sections.append(m_sections[-1] + m_)
            n_sections.append(n_sections[-1] + n_)
        m_sections.append(m)
        n_sections.append(n)
        self.binary_c = np.zeros((m, n), dtype=np.uint8)
        size_slide = 20
        for i in range(len(m_sections) - 1):
            for j in range(len(n_sections) - 1):
                if m_sections[i] == 0:
                    m_window_i, m_window_e = 0, m_sections[i + 1] + size_slide
                elif m_sections[i + 1] == m:
                    m_window_i, m_window_e = m_sections[i] - size_slide, m_sections[i + 1]
                else:
                    m_window_i, m_window_e = m_sections[i] - size_slide, m_sections[i + 1] + size_slide
                if n_sections[j] == 0:
                    n_window_i, n_window_e = 0, n_sections[j + 1] + size_slide
                elif n_sections[j + 1] == n:
                    n_window_i, n_window_e = n_sections[j] - size_slide, n_sections[j + 1]
                else:
                    n_window_i, n_window_e = n_sections[j] - size_slide, n_sections[j + 1] + size_slide
                m_s, n_s = int(m_window_e - m_window_i), int(n_window_e - n_window_i)
                roi_binary = np.zeros((int(m_s), int(n_s)), dtype=np.uint8)
                roi_binary[:, :] = binary_[int(m_window_i):int(m_window_e), int(n_window_i):int(n_window_e)]
                roi_area = len(np.where(roi_binary == 255)[0])
                relation = roi_area / total_area
                if relation < 0.30:
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    roi_ = cv2.morphologyEx(roi_binary, cv2.MORPH_DILATE, kernel, iterations=1)
                    arr = roi_ > 0
                    roi_ = morphology.remove_small_objects(arr, min_size=2000, connectivity=1)
                    roi_ = roi_.astype(np.uint8)
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    roi_ = cv2.morphologyEx(roi_, cv2.MORPH_DILATE, kernel, iterations=1)
                    roi_ = morphology.remove_small_holes(roi_.astype(np.bool_), area_threshold=min_area_,
                                                         connectivity=1)
                    arr = roi_ > 0
                    roi_ = morphology.remove_small_objects(arr, min_size=1000, connectivity=1)
                else:
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    roi_ = cv2.morphologyEx(roi_binary, cv2.MORPH_DILATE, kernel, iterations=2)
                    roi_ = morphology.remove_small_holes(roi_.astype(np.bool_), area_threshold=min_area_,
                                                         connectivity=1)
                    arr = roi_ > 0
                    roi_ = morphology.remove_small_objects(arr, min_size=2000, connectivity=1)
                    roi_ = roi_.astype(np.uint8)
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                    roi_ = cv2.morphologyEx(roi_, cv2.MORPH_DILATE, kernel, iterations=1)
                    roi_ = morphology.remove_small_holes(roi_.astype(np.bool_), area_threshold=min_area_,
                                                         connectivity=1)
                    arr = roi_ > 0
                    roi_ = morphology.remove_small_objects(arr, min_size=3000, connectivity=1)
                roi_ = roi_.astype(np.uint8)
                self.binary_c[int(m_window_i):int(m_window_e), int(n_window_i):int(n_window_e)] = roi_
        return self.binary_c

    def gema_cells_bf(self, image_, final_img_, sections_):
        # Gabor image
        gabor_img = self.apply_gabor(final_img_, self.filters_)
        # evaluate area
        thresh = self.sobel_ima(gabor_img, sections_)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh_ = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel, iterations=1)
        thresh_ = morphology.remove_small_holes(thresh_.astype(np.bool_), area_threshold=1500, connectivity=2)
        thresh_ = thresh_.astype(np.uint8)
        percent_, _ = self.compute_percent_area(thresh_, 0)
        ctr_ = False
        if percent_ > 50:
            thresh = self.sobel_ima(gabor_img, 35)
            ctr_ = True
        min_area_holes = 1500 if not ctr_ else 750
        binary_ = self.image_sections_bf(gabor_img, thresh, 2, min_area_holes)
        image_out_, binary_n, areas = self.generate_contour(image_, binary_)
        percent_, area_ = self.compute_percent_area(binary_n, areas)
        return image_out_, binary_n, percent_, area_, len(areas)

    def main(self, img_, name_, sections, results):
        tic = time.process_time()
        final_img_cc = self.preprocessing(img_)
        area_t_ = np.round(((final_img_cc.shape[0] / 4) * (final_img_cc.shape[1] / 4)), 2)
        # gema for cells
        image_out_cc, binary_cc, percent_cc, area_cc, regions = self.gema_cells_bf(img_, final_img_cc, sections)
        print("")
        table = [['Image CC name       : ', name_],
                 ['Percentage CC value : ', str(percent_cc)]]
        for line in table:
            print('{:>10} {:>10}'.format(*line))
        print('')
        time_p = np.round(time.process_time() - tic, 2)
        print('Time used by GEMA     : ' + str(time_p) + ' sec.')
        # save results
        new_row = pd.DataFrame.from_records([{'Image': name_, 'Regions': regions, 'Percentage Area': percent_cc,
                                              'Image Area (um2)': area_t_, 'Detected Area (um2)': area_cc,
                                              'Time (sec)': time_p}])

        if results.empty:
            results = new_row.copy()
        else:
            results = pd.concat([results, new_row], ignore_index=True)

        self.window['_TAR_'].update(area_t_)
        self.window['_DAR_'].update(area_cc)
        self.window['_PAR_'].update(percent_cc)
        self.window['_SPH_'].update(regions)
        self.window['_TUS_'].update(time_p)

        return image_out_cc, binary_cc, results




