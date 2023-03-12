from collections import deque


class SlidingWindow:
    window_size = 20
    acc_x = deque()
    acc_y = deque()
    acc_z = deque()

    def __int__(self):
        """
        Keep a window of size determined by the size parameter
        :return: An object of SlidingWindow
        """
        self.acc_x = deque()
        self.acc_y = deque()
        self.acc_z = deque()

    def update_window_size(self, size):
        """
        Change the size of the window, will clear the window as well
        :param size: The new size required
        :return: None
        """
        self.window_size = size

    def update_window(self, raw_data):
        """
        Update the current window by appending the new data and removing the old data
        :param raw_data: Expect an array of size 3 which corresponds to accelerometer reading of a single data point
        :return: None
        """
        if len(self.acc_x) == self.window_size:
            self.acc_x.popleft()
            self.acc_y.popleft()
            self.acc_z.popleft()
        self.acc_x.append(raw_data[0])
        self.acc_y.append(raw_data[1])
        self.acc_z.append(raw_data[2])

    def get_curr_value(self):
        """
        Get the threshold value of the current sliding window
        :return: The threshold value of the current sliding window, or 0 if window is empty
        """
        if len(self.acc_x) == 0:
            return 0
        return max(self.acc_x) - min(self.acc_x) + max(self.acc_y) - min(self.acc_y) + max(self.acc_z) - min(self.acc_z)

    def clear_window(self):
        """
        Remove all data stored in the window
        :return: None
        """
        self.acc_x.clear()
        self.acc_y.clear()
        self.acc_z.clear()

    def fill_window(self, raw_data):
        """
        Fill the window by the raw data
        :param raw_data: Expect a raw data contains at least self.window_size data points
        :return: None
        """
        for datapoint in raw_data[:5]:
            self.update_window(datapoint[:3])
