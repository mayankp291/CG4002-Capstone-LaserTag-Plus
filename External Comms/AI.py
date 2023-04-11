from pynq import Overlay
from pynq import allocate
import numpy as np
from multiprocessing import Process, Queue

from scipy.stats import skew
from scipy.fftpack import fft

NUM_OUTPUT = 1
NUM_FEATURES = 8
NUM_INPUT = NUM_FEATURES * 6


class AI_Process(Process):
    def __init__(self, q):
        super().__init__()
        # DMA BUFFER CONFIG
        self.ol = Overlay('new_design_1_wrapper.bit')
        self.dma = self.ol.axi_dma_0
        self.input_buffer = allocate(shape=(NUM_INPUT), dtype=np.int32)
        self.output_buffer = allocate(shape=(NUM_OUTPUT,), dtype=np.int32)
        self.imu_data = np.empty((40,6), dtype=np.int32)
        self.imu_queue = q
        self.player = None
        self.features = None


    def run(self):
        while True:
            self.player, self.imu_data = self.imu_queue.get()
            self.AI_actual()
                
    def extract_features(self):

        mean_acc_x = np.mean(self.imu_data[0])
        mean_acc_y = np.mean(self.imu_data[1])
        mean_acc_z = np.mean(self.imu_data[2])
        mean_gyro_x = np.mean(self.imu_data[3])
        mean_gyro_y = np.mean(self.imu_data[4])
        mean_gyro_z = np.mean(self.imu_data[5])

        sd_acc_x = np.std(self.imu_data[0])
        sd_acc_y = np.std(self.imu_data[1])
        sd_acc_z = np.std(self.imu_data[2])
        sd_gyro_x = np.std(self.imu_data[3])
        sd_gyro_y = np.std(self.imu_data[4])
        sd_gyro_z = np.std(self.imu_data[5])

        max_acc_x = np.amax(self.imu_data[0])
        max_acc_y = np.amax(self.imu_data[1])
        max_acc_z = np.amax(self.imu_data[2])
        max_gyro_x = np.amax(self.imu_data[3])
        max_gyro_y = np.amax(self.imu_data[4])
        max_gyro_z = np.amax(self.imu_data[5])

        min_acc_x = np.amin(self.imu_data[0])
        min_acc_y = np.amin(self.imu_data[1])
        min_acc_z = np.amin(self.imu_data[2])
        min_gyro_x = np.amin(self.imu_data[3])
        min_gyro_y = np.amin(self.imu_data[4])
        min_gyro_z = np.amin(self.imu_data[5])

        rms_acc_x = np.sqrt(np.mean(self.imu_data[0] ** 2))
        rms_acc_y = np.sqrt(np.mean(self.imu_data[1] ** 2))
        rms_acc_z = np.sqrt(np.mean(self.imu_data[2] ** 2))
        rms_gyro_x = np.sqrt(np.mean(self.imu_data[3] ** 2))
        rms_gyro_y = np.sqrt(np.mean(self.imu_data[4] ** 2))
        rms_gyro_z = np.sqrt(np.mean(self.imu_data[5] ** 2))

        skew_acc_x = skew(self.imu_data[0])
        skew_acc_y = skew(self.imu_data[1])
        skew_acc_z = skew(self.imu_data[2])
        skew_gyro_x = skew(self.imu_data[3])
        skew_gyro_y = skew(self.imu_data[4])
        skew_gyro_z = skew(self.imu_data[5])

        mag_acc_x = np.amax(np.abs(fft(self.imu_data[0])))
        mag_acc_y = np.amax(np.abs(fft(self.imu_data[1])))
        mag_acc_z = np.amax(np.abs(fft(self.imu_data[2])))
        mag_gyro_x = np.amax(np.abs(fft(self.imu_data[3])))
        mag_gyro_y = np.amax(np.abs(fft(self.imu_data[4])))
        mag_gyro_z = np.amax(np.abs(fft(self.imu_data[5])))

        phase_acc_x = np.amax(np.angle(fft(self.imu_data[0])))
        phase_acc_y = np.amax(np.angle(fft(self.imu_data[1])))
        phase_acc_z = np.amax(np.angle(fft(self.imu_data[2])))
        phase_gyro_x = np.amax(np.angle(fft(self.imu_data[3])))
        phase_gyro_y = np.amax(np.angle(fft(self.imu_data[4])))
        phase_gyro_z = np.amax(np.angle(fft(self.imu_data[5])))

        self.features = np.array([mean_acc_x, mean_acc_y, mean_acc_z, mean_gyro_x, mean_gyro_y, mean_gyro_z, sd_acc_x,
                               sd_acc_y, sd_acc_z, sd_gyro_x, sd_gyro_y, sd_gyro_z,
                               max_acc_x, max_acc_y, max_acc_z, max_gyro_x, max_gyro_y, max_gyro_z,
                               min_acc_x, min_acc_y, min_acc_z, min_gyro_x, min_gyro_y, min_gyro_z,
                               rms_acc_x, rms_acc_y, rms_acc_z, rms_gyro_x, rms_gyro_y, rms_gyro_z,
                               skew_acc_x, skew_acc_y, skew_acc_z, skew_gyro_x, skew_gyro_y, skew_gyro_z,
                               mag_acc_x, mag_acc_y, mag_acc_z, mag_gyro_x, mag_gyro_y, mag_gyro_z,
                               phase_acc_x, phase_acc_y, phase_acc_z, phase_gyro_x, phase_gyro_y, phase_gyro_z]).astype(np.int32)
        

    def detect_start_of_move(self):

        # define threshold values as hard-coded values
        ## OLD
        # x_thresh = 18300
        # y_thresh = 11000
        # z_thresh = 17000
        
        # ## NEW
        # x_thresh = 19300
        # y_thresh = 15000
        # z_thresh = 18000

        ## TEST
        x_thresh = 19300
        y_thresh = 13000
        z_thresh = 18000   

        # x_thresh = 15300
        # y_thresh = 9000
        # z_thresh = 18000 

        # x_thresh = y_thresh = z_thresh = 9000

        # np_imu_data = np.array(self.imu_data)

        # compare each data point in window to threshold
        for j in range(self.imu_data.shape[0]):
            acc_vals = self.imu_data[j, :3]

            if (abs(acc_vals[0]) > x_thresh) or (abs(acc_vals[1]) > y_thresh) or (abs(acc_vals[2]) > z_thresh):
                # potential start of move action identified
                # check next few data points to confirm start of move action
                for k in range(j+1, j+4):
                    try:
                        next_acc_vals = self.imu_data[k, :3]

                    except IndexError:
                        # if index is out of range, move to next window
                        break

                    if not ((abs(next_acc_vals[0]) > x_thresh) or (abs(next_acc_vals[1]) > y_thresh) or (abs(next_acc_vals[2]) > z_thresh)):
                        # not the start of move action, move to next window
                        break
                else:
                    # confirmed start of move action
                    # np_imu_data = np_imu_data[j:]
                    # print("Start of move action detected", self.imu_data.shape)
                    self.imu_data = np.transpose(self.imu_data)
                    # print(self.imu_data.shape)
                    return 
                    # return self.imu_data.T

        # return None
        self.imu_data = None


    def detect_start_of_move2(self, imu_data):

        ## TEST
        x_thresh = 19300
        y_thresh = 13000
        z_thresh = 18000   

        np_imu_data = np.array(imu_data)

        # compare each data point in window to threshold
        abs_acc_vals = np.abs(np_imu_data[:, :3])
        mask = (abs_acc_vals > [x_thresh, y_thresh, z_thresh]).any(axis=1)
        idx = np.argmax(mask)
        if mask[idx]:
            # potential start of move action identified
            # check next few data points to confirm start of move action
            k = min(idx+4, np_imu_data.shape[0])

            # Try the below two lines for mask and see if either one is correct
            mask = (abs_acc_vals[idx+1:k] > [x_thresh, y_thresh, z_thresh]).any(axis=1)

            # mask = (np.abs(np_imu_data[idx+1:k, :3]) > [x_thresh, y_thresh, z_thresh]).any(axis=1)
            if not mask.any():
                # confirmed start of move action
                # np_imu_data = np_imu_data[idx:]
                return np_imu_data.T

        return None
    

    def detect_start_of_move3(self):
        x_thresh = 19300
        y_thresh = 13000
        z_thresh = 18000   

        np_imu_data = np.array(self.imu_data)

        # Sliding window approach with window size of 5
        window_size = 5
        for j in range(0, np_imu_data.shape[0] - window_size + 1, window_size):
            acc_vals = np_imu_data[j:j+window_size, :3]
            
            # Check if any of the values in the window exceed the threshold
            if (np.abs(acc_vals) > [x_thresh, y_thresh, z_thresh]).any():
                # potential start of move action identified
                # Check next few windows to confirm start of move action
                for k in range(j+window_size, j+window_size*4, window_size):
                    next_acc_vals = np_imu_data[k:k+window_size, :3]
                    if not (np.abs(next_acc_vals) > [x_thresh, y_thresh, z_thresh]).any():
                        # not the start of move action, move to next window
                        break
                else:
                    # confirmed start of move action
                    np_imu_data = np_imu_data[j:]
                    return np_imu_data.T

        return None



    def AI_actual(self):
        global prediction_array, NUM_INPUT
        
        self.detect_start_of_move()

        if self.imu_data is None:
            return None

        mapping = {0: 'logout', 1: 'shield', 2: 'reload', 3: 'grenade', 4: 'idle'}
        self.extract_features()

        for i in range(NUM_INPUT):
            self.input_buffer[i] = self.features[i]

        run = True
        while run:
            try:
                # aiflag.clear()
                self.dma.sendchannel.transfer(self.input_buffer)
                self.dma.recvchannel.transfer(self.output_buffer)
                self.dma.sendchannel.wait()
                self.dma.recvchannel.wait()

                action = self.output_buffer[0]

                # prediction_array.append(action)
                print('Predicted class:', self.player, action, mapping[action])
                
                run = False
                if not mapping[action] == 'idle':
                    self.imu_queue.put(mapping[action])

            except RuntimeError as e:
                print(e)
                break