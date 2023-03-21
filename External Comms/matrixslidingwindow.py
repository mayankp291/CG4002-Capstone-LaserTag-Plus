from collections import deque
import numpy as np

class MatrixSlidingWindow:
    def __init__(self, window_size):
        self.window_size = window_size
        self.matrix = deque(maxlen=window_size)
        self.acc_mean = np.zeros(3)
        self.acc_std = np.zeros(3)
        self.prev_means = []
        self.prev_mean_len = 5
        self.move_started = False  # flag to indicate if move started
        self.move_start_matrix = None  # matrix that triggered the start of move

    def add_new_matrix(self, new_data):
        self.matrix.append(new_data)
        
        # update mean and std
        self.acc_mean = np.mean(np.array(self.matrix)[:, :, :3], axis=(0, 1))
        self.acc_std = np.std(np.array(self.matrix)[:, :, :3], axis=(0, 1))
        
        # update previous means
        if len(self.prev_means) >= self.prev_mean_len:
            self.prev_means.pop(0)
        self.prev_means.append(self.acc_mean)
            
        # check if start of move detected
        if not self.move_started and self.is_start_of_move():
            self.move_started = True
            self.move_start_matrix = np.array(self.matrix)
            
    def clear(self):
        self.matrix.clear()
        self.acc_mean = np.zeros(3)
        self.acc_std = np.zeros(3)
        self.prev_means = []
        self.move_started = False
        self.move_start_matrix = None
        
    def is_full(self):
        return len(self.matrix) == self.window_size
    
    def remove_old_value(self):
        self.matrix.popleft()
        
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
                    next_acc_vals = np.array(self.matrix)[-k, :, :3].mean(axis=0)

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
        

    def is_move_detected(self):
        # define threshold values as hard-coded values
        x_thresh = 13000
        y_thresh = 5000
        z_thresh = 19000

        matrix = self.data.popleft()

        # compare each data point in window to threshold
        for j in range(matrix.shape[0]):
            acc_vals = np.array(self.matrix)[j, :3]

            if (abs(acc_vals[0]) > x_thresh) or (abs(acc_vals[1]) > y_thresh) or (abs(acc_vals[2]) > z_thresh):
                # potential start of move action identified
                # check next few data points to confirm start of move action
                for k in range(j+1, j+4):
                    try:
                        next_acc_vals = np.array(self.matrix)[k, :3]

                    except IndexError:
                        # if index is out of range, move to next window
                        break

                    if not ((abs(next_acc_vals[0]) > x_thresh) or (abs(next_acc_vals[1]) > y_thresh) or (abs(next_acc_vals[2]) > z_thresh)):
                        # not the start of move action, move to next window
                        break
                else:
                    # confirmed start of move action
                    return True
        return False