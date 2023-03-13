from collections import deque
import numpy as np

class SlidingWindow:
    def __init__(self, window_size):
        self.window_size = window_size
        self.data = deque(maxlen=window_size)
        self.acc_mean = np.zeros(3)
        self.acc_std = np.zeros(3)
        self.gyro_mean = np.zeros(3)
        self.gyro_std = np.zeros(3)
        

    def fill(self, new_data):
        self.data.extend(np.array(new_data))
        
        # update mean and std
        self.acc_mean = np.mean(np.array(self.data)[:, :3], axis=0)
        self.acc_std = np.std(np.array(self.data)[:, :3], axis=0)
        self.gyro_mean = np.mean(np.array(self.data)[:, 3:], axis=0)
        self.gyro_std = np.std(np.array(self.data)[:, 3:], axis=0)
            

    def clear(self):
        self.data.clear()
        self.acc_mean = np.zeros(3)
        self.acc_std = np.zeros(3)
        self.gyro_mean = np.zeros(3)
        self.gyro_std = np.zeros(3)
        

    def add_new_value(self, new_value):
        if self.is_full():
            self.data.popleft()

        self.data.append(new_value)
    

    def update_threshold(self):
        # update mean and std
        self.acc_mean = np.mean(np.array(self.data)[:, :3], axis=0)
        self.acc_std = np.std(np.array(self.data)[:, :3], axis=0)
        self.gyro_mean = np.mean(np.array(self.data)[:, 3:], axis=0)
        self.gyro_std = np.std(np.array(self.data)[:, 3:], axis=0)


    def is_full(self):
        return len(self.data) == self.window_size
    

    def remove_old_value(self):
        self.data.popleft()

        
    def is_start_of_move(self):
        # define threshold values as 2 standard deviations away from the mean
        acc_thresh = 2 * self.acc_std
        gyro_thresh = 2 * self.gyro_std
        
        # compare each data point in window to threshold
        for j in range(self.window_size):
            acc_vals = np.array(self.data)[j, :3]
            gyro_vals = np.array(self.data)[j, 3:]
            
            if ((acc_vals > self.acc_mean + acc_thresh).all() and (gyro_vals > self.gyro_mean + gyro_thresh).all()) or ((acc_vals < self.acc_mean - acc_thresh).all() and (gyro_vals < self.gyro_mean - gyro_thresh).all()):
                # potential start of move action identified
                # check next few data points to confirm start of move action
                for k in range(j+1, j+4):
                    try:
                        next_acc_vals = np.array(self.data)[k, :3]
                        next_gyro_vals = np.array(self.data)[k, 3:]
                    except IndexError:
                        # if index is out of range, move to next window
                        break

                    if not ((next_acc_vals > self.acc_mean + acc_thresh).all() and (next_gyro_vals > self.gyro_mean + gyro_thresh).all() or (next_acc_vals < self.acc_mean - acc_thresh).all() and (next_gyro_vals < self.gyro_mean - gyro_thresh).all()):
                        # not the start of move action, move to next window
                        break
                else:
                    # confirmed start of move action
                    return True
                    # return j
        return False
        # return -1


    def get_window_matrix(self):    
        window_matrix = np.array(self.data)
        # pad with zeros if data is less than window size
        if window_matrix.shape[0] < self.window_size:
            pad_size = self.window_size - window_matrix.shape[0]
            padding = np.zeros((pad_size, window_matrix.shape[1]))
            window_matrix = np.concatenate((padding, window_matrix), axis=0)
        return window_matrix.T
