import pynq.ps
import sys, inspect


def print_classes():
    for name, obj in inspect.getmembers(sys.modules['pynq.ps']):
        if inspect.isclass(obj):
            print(obj)


# lower clock frequency for PL
def lower_PL_clk_rate():
    """
    Lower the unused clock frequency to save power
    :return: None
    """
    pynq.ps.Clocks.fclk0_mhz = 5
    pynq.ps.Clocks.fclk1_mhz = 1
    pynq.ps.Clocks.fclk2_mhz = 1
    pynq.ps.Clocks.fclk3_mhz = 1


        # loaded = []
        # tmean = mean(raw_axis_data)
        # tstd = std(raw_axis_data)
        # t25percentile = percentile(raw_axis_data, 25)
        # trms = sqrt(mean(sum(data**2 for data in raw_axis_data)))
        # tskew = skew(raw_axis_data)
        # temp = [tmean, tstd, t25percentile, trms, tskew]
        # # convert to frequency domain by FFT
        # freq_domain = np.fft.rfft(raw_axis_data)
        # fmax = abs(max(freq_domain))
        # fmin = abs(min(freq_domain))
        # energy = sum(abs(freq_domain) ** 2) / 100 ** 2
        # freq_temp = [fmax, fmin, energy]
        # temp.extend(freq_temp)
        # loaded.extend(temp)


