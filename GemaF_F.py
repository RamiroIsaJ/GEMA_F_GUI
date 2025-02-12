# Ramiro Isa-Jara, ramiro.isaj@gmail.com
# Interface GEMA_F - CELL Analysis in Bright and Fluorescent Fields
import cv2
import time
import numpy as np
import pandas as pd
from skimage import morphology
from skimage.filters import threshold_otsu
from skimage.filters import threshold_multiotsu


class GemaFFluorescent:
    def __init__(self, window):
        self.window = window
        self.filters_ = []
        self.condition, self.control, self.factor_ = None, False, False
        self.gabor_img_, self.final_img_, self.binary_c = None, None, None

    def preprocessing(self, img):
        alpha, beta = 6.5, 12.5
        img_ = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        image_gray_ = cv2.cvtColor(img_, cv2.COLOR_BGR2GRAY)
        clh = cv2.createCLAHE(clipLimit=5.0)
        image_gray_ = clh.apply(image_gray_)
        self.final_img_ = cv2.GaussianBlur(image_gray_, (5, 5), 0)
        return self.final_img_

    def build_filters(self,):
        k_size, sigma = 21, 2.5
        for theta in np.arange(0, np.pi, np.pi / 16):
            kern = cv2.getGaborKernel((k_size, k_size), sigma, theta, 11.0, 0.5, 0, ktype=cv2.CV_32F)
            kern /= 3.8 * kern.sum()
            self.filters_.append(kern)

    def apply_gabor(self, img, filters):
        self.gabor_img_ = np.zeros_like(img)
        for kern in filters:
            np.maximum(self.gabor_img_, cv2.filter2D(img, cv2.CV_8UC3, kern), self.gabor_img_)
        return self.gabor_img_

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
        valid_contour, error_contour, area_valid, area_error = [], [], [], []
        for c in contours:
            area = cv2.contourArea(c)
            if area > 100:
                if self.verify_contour(c):
                    valid_contour.append(c)
                    area_valid.append(area/16)
                else:
                    error_contour.append(c)
                    area_error.append(area)
        return valid_contour, error_contour, np.array(area_valid), np.array(area_error),

    @staticmethod
    def delete_regions(binary_, areas_error_, e_contours_):
        # delete binary
        if len(e_contours_) > 0:
            contours_ = np.copy(e_contours_[0])
            for i in range(len(areas_error_)):
                if areas_error_[i] <= 5000:
                    cv2.fillPoly(binary_, pts=[contours_[i]], color=(0, 0, 0))
        return binary_

    def generate_contour(self, img, mark):
        binary = mark.copy()
        ima_sel_ = img.copy()
        ima_sel_[mark == 0] = 0
        v_contours, e_contours, area_contours, area_error_ = self.calculate_contour(mark)
        color1 = (0, 255, 0)
        # draw contours
        cv2.drawContours(ima_sel_, v_contours, -1, color1, 3)
        binary = self.delete_regions(binary, area_error_, e_contours)
        return ima_sel_, binary, area_contours

    def image_sections_ff(self, image_ff, sections_):
        m, n = image_ff.shape
        m_, n_ = np.round(m / sections_), np.round(n / sections_)
        m_sections, n_sections = [0], [0]
        for i in range(sections_ - 1):
            m_sections.append(m_sections[-1] + m_)
            n_sections.append(n_sections[-1] + n_)
        m_sections.append(m)
        n_sections.append(n)
        self.binary_c = np.zeros((m, n), dtype=np.uint8)
        if self.factor_:
            factor = 3.4 if threshold_otsu(image_ff) <= 20 else 5.3
            factor = factor + 1.0 if threshold_otsu(image_ff) >= 28 else factor
        else:
            factor = 1.0 if threshold_otsu(image_ff) < 30 else 2.0
        size_slide = 5
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
                roi_image = np.zeros((int(m_s), int(n_s)), dtype=np.uint8)
                roi_image[:, :] = image_ff[int(m_window_i):int(m_window_e), int(n_window_i):int(n_window_e)]
                thresholds = np.array(threshold_multiotsu(roi_image))
                thresholds = thresholds + factor if thresholds[1] - thresholds[0] < 15 else thresholds + (factor/2)
                binary_ = np.digitize(roi_image, bins=thresholds)
                binary_ = binary_.astype(np.uint8)
                self.binary_c[int(m_window_i):int(m_window_e), int(n_window_i):int(n_window_e)] = binary_[:, :]
        return self.binary_c

    def gema_cells(self, image_, final_img_, sections_):
        if self.control is False:
            if threshold_otsu(final_img_) <= 80:
                self.factor_, self.control = True, True
        # Gabor image
        gabor_img = self.apply_gabor(final_img_, self.filters_)
        # evaluate area
        thresh = self.image_sections_ff(gabor_img, sections_)
        # apply morphology operations in thresh image
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary_ = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary_ = cv2.morphologyEx(binary_, cv2.MORPH_CLOSE, kernel, iterations=1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        binary_ = cv2.morphologyEx(binary_, cv2.MORPH_OPEN, kernel, iterations=2)
        arr = binary_ > 0
        binary_ = morphology.remove_small_objects(arr, min_size=500, connectivity=2)
        binary_ = morphology.remove_small_holes(binary_.astype(np.bool_), area_threshold=3000, connectivity=1)
        binary_ = binary_.astype(np.uint8)
        image_out_, binary_n, areas = self.generate_contour(image_, binary_)
        percent_, area_ = self.compute_percent_area(binary_n, areas)
        return image_out_, binary_n, percent_, area_, len(areas)

    def main(self, i, img_, name_, sections, results):
        tic = time.process_time()
        final_img_ff = self.preprocessing(img_)
        area_t_ = np.round(((final_img_ff.shape[0] / 4) * (final_img_ff.shape[1] / 4)), 2)
        # gema for cells
        image_out_ff, binary_ff, percent_ff, area_ff, regions = self.gema_cells(img_, final_img_ff, sections)
        print("")
        table = [['Image FF name       : ', name_],
                 ['Percentage FF value : ', str(percent_ff)]]
        for line in table:
            print('{:>10} {:>10}'.format(*line))
        print('')
        time_p = np.round(time.process_time() - tic, 2)
        print('Time used by GEMA     : ' + str(time_p) + ' sec.')
        # save results
        new_row = pd.DataFrame.from_records([{'Image': name_, 'Regions': regions, 'Percentage Area': percent_ff,
                                              'Image Area (um2)': area_t_, 'Detected Area (um2)': area_ff,
                                              'Time (sec)': time_p}])
        if results.empty:
            results = new_row.copy()
        else:
            results = pd.concat([results, new_row], ignore_index=True)

        self.window['_TAR_'].update(area_t_)
        self.window['_DAR_'].update(area_ff)
        self.window['_PAR_'].update(percent_ff)
        self.window['_SPH_'].update(regions)
        self.window['_TUS_'].update(time_p)

        return image_out_ff, binary_ff, results
