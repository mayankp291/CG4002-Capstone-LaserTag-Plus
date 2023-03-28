from collections import deque
import numpy as np

class MatrixSlidingWindow:
    def __init__(self, window_size):
        self.window_size = window_size
        self.data = deque(maxlen=window_size)
        self.acc_mean = np.zeros(3)
        self.acc_std = np.zeros(3)
        self.prev_means = []
        self.prev_mean_len = 5
        self.move_started = False  # flag to indicate if move started
        self.move_start_matrix = None  # matrix that triggered the start of move

    def fill(self, new_data):
        self.data.append(new_data)
        
        # update mean and std
        self.acc_mean = np.mean(np.array(self.data)[:, :, :3], axis=(0, 1))
        self.acc_std = np.std(np.array(self.data)[:, :, :3], axis=(0, 1))
        
        # update previous means
        if len(self.prev_means) >= self.prev_mean_len:
            self.prev_means.pop(0)
        self.prev_means.append(self.acc_mean)
            
        # check if start of move detected
        if not self.move_started and self.is_start_of_move():
            self.move_started = True
            self.move_start_matrix = np.array(self.data)
            
    def clear(self):
        self.data.clear()
        self.acc_mean = np.zeros(3)
        self.acc_std = np.zeros(3)
        self.prev_means = []
        self.move_started = False
        self.move_start_matrix = None
        
    def is_full(self):
        return len(self.data) == self.window_size
    
    def remove_old_value(self):
        self.data.popleft()
        
    def is_start_of_move(self):
        if len(self.prev_means) < self.prev_mean_len:
            return False

        # define threshold values as 2 standard deviations away from the mean
        acc_thresh = 2 * self.acc_std

        # compare the mean of the acceleration values in the current window to the means of the previous windows
        prev_means = np.array(self.prev_means)
        prev_means_mean = np.mean(prev_means, axis=0)

        if (self.acc_mean > prev_means_mean + acc_thresh).all() or (self.acc_mean < prev_means_mean - acc_thresh).all():
            # potential start of move action identified
            # check next few data points to confirm start of move action
            for k in range(1, 4):
                try:
                    next_acc_vals = np.array(self.data)[-k, :, :3].mean(axis=0)

                except IndexError:
                    # if index is out of range, move to next window
                    break

                if not ((next_acc_vals > prev_means_mean + acc_thresh).all() or (next_acc_vals < prev_means_mean - acc_thresh).all()):
                    # not the start of move action, move to next window
                    break
            else:
                # confirmed start of move action
                return True

        return False
    
    def get_move_start_matrix(self):
        if self.move_started:
            return self.move_start_matrix
        else:
            return None
