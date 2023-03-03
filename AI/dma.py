from pynq import Overlay
from pynq import allocate
import numpy as np

NUM_OUTPUT = 1

def extract_features(input):

    mean_acc_x = np.mean(input[0], axis=1).reshape(-1,1)
    mean_acc_y = np.mean(input[1], axis=1).reshape(-1,1)
    mean_acc_z = np.mean(input[2], axis=1).reshape(-1,1)
    mean_gyro_x = np.mean(input[3], axis=1).reshape(-1,1)
    mean_gyro_y = np.mean(input[4], axis=1).reshape(-1,1)
    mean_gyro_z = np.mean(input[5], axis=1).reshape(-1,1)


    sd_precision = 100000
    sd_acc_x = np.std(input[0], axis=1).reshape(-1,1) * sd_precision
    sd_acc_y = np.std(input[1], axis=1).reshape(-1,1) * sd_precision
    sd_acc_z = np.std(input[2], axis=1).reshape(-1,1) * sd_precision
    sd_gyro_x = np.std(input[3], axis=1).reshape(-1,1) * sd_precision
    sd_gyro_y = np.std(input[4], axis=1).reshape(-1,1) * sd_precision
    sd_gyro_z = np.std(input[5], axis=1).reshape(-1,1) * sd_precision

    max_acc_x = np.amax(input[0], axis=1).reshape(-1,1)
    max_acc_y = np.amax(input[1], axis=1).reshape(-1,1)
    max_acc_z = np.amax(input[2], axis=1).reshape(-1,1)
    max_gyro_x = np.amax(input[3], axis=1).reshape(-1,1)
    max_gyro_y = np.amax(input[4], axis=1).reshape(-1,1)
    max_gyro_z = np.amax(input[5], axis=1).reshape(-1,1)

    min_acc_x = np.amin(input[0], axis=1).reshape(-1,1)
    min_acc_y = np.amin(input[1], axis=1).reshape(-1,1)
    min_acc_z = np.amin(input[2], axis=1).reshape(-1,1)
    min_gyro_x = np.amin(input[3], axis=1).reshape(-1,1)
    min_gyro_y = np.amin(input[4], axis=1).reshape(-1,1)
    min_gyro_z = np.amin(input[5], axis=1).reshape(-1,1)

    rms_precision = 100000
    rms_acc_x = np.sqrt(np.mean(input[0]**2, axis=1), axis=1) * rms_precision
    rms_acc_y = np.sqrt(np.mean(input[1]**2, axis=1), axis=1) * rms_precision
    rms_acc_z = np.sqrt(np.mean(input[2]**2, axis=1), axis=1) * rms_precision
    rms_gyro_x = np.sqrt(np.mean(input[3]**2, axis=1), axis=1) * rms_precision
    rms_gyro_y = np.sqrt(np.mean(input[4]**2, axis=1), axis=1) * rms_precision
    rms_gyro_z = np.sqrt(np.mean(input[5]**2, axis=1), axis=1) * rms_precision

    skew_acc_x = skew(input[0], axis=1)
    skew_acc_y = skew(input[1], axis=1)
    skew_acc_z = skew(input[2], axis=1)
    skew_gyro_x = skew(input[3], axis=1)
    skew_gyro_y = skew(input[4], axis=1)
    skew_gyro_z = skew(input[5], axis=1)

    # Convert to frequency domain
    signal_acc_x = fft(input[0], axis=1)
    signal_acc_y = fft(input[1], axis=1)
    signal_acc_z = fft(input[2], axis=1)
    signal_gyro_x = fft(input[3], axis=1)
    signal_gyro_y = fft(input[4], axis=1)
    signal_gyro_z = fft(input[5], axis=1)

    mag_precision = 10000
    mag_acc_x = np.amax(np.abs(signal_acc_x), axis=1) * mag_precision
    mag_acc_y = np.amax(np.abs(signal_acc_y), axis=1) * mag_precision
    mag_acc_z = np.amax(np.abs(signal_acc_z), axis=1) * mag_precision
    mag_gyro_x = np.amax(np.abs(signal_gyro_x), axis=1) * mag_precision
    mag_gyro_y = np.amax(np.abs(signal_gyro_y), axis=1) * mag_precision
    mag_gyro_z = np.amax(np.abs(signal_gyro_z), axis=1) * mag_precision


    phase_precision = 10000
    phase_acc_x = np.amax(np.angle(signal_acc_x), axis=1) * phase_precision
    phase_acc_y = np.amax(np.angle(signal_acc_y), axis=1) * phase_precision
    phase_acc_z = np.amax(np.angle(signal_acc_z), axis=1) * phase_precision
    phase_gyro_x = np.amax(np.angle(signal_gyro_x), axis=1) * phase_precision
    phase_gryo_y = np.amax(np.angle(signal_gyro_y), axis=1) * phase_precision
    phase_gyro_z = np.amax(np.angle(signal_gyro_z), axis=1) * phase_precision
    

    return np.concatenate((mean_acc_x, mean_acc_y, mean_acc_z, mean_gyro_x, mean_gyro_y, mean_gyro_z,         sd_acc_x, sd_acc_y, sd_acc_z, sd_gyro_x, sd_gyro_y, sd_gyro_z, 
    max_acc_x, max_acc_y, max_acc_z, max_gyro_x, max_gyro_y, max_gyro_z,
    min_acc_x, min_acc_y, min_acc_z, min_gyro_x, min_gyro_y, min_gyro_z, 
    rms_acc_x, rms_acc_y, rms_acc_z, rms_gyro_x, rms_gyro_y, rms_gyro_z, 
    skew_acc_x, skew_acc_y, skew_acc_z, skew_gyro_x, skew_gyro_y, skew_gyro_z,
    mag_acc_x, mag_acc_y, mag_acc_z, mag_gyro_x, mag_gyro_y, mag_gyro_z,
    phase_acc_x, phase_acc_y, phase_acc_z, phase_gyro_x, phase_gyro_y, phase_gyro_z), axis=1)

def dma(input):

    # Line 13 and 14 (two lines below to be removed and add to main configuration/inital setup when starting script)
    ol = Overlay('design_1_wrapper.bit')
    dma = ol.axi_dma_0

    features = extract_features(input)

    run = True

    input_buffer = allocate(shape=(len(features),), dtype=np.int16)
    output_buffer = allocate(shape=(NUM_OUTPUT,), dtype=np.int16)

    for i in range(len(features)):
        input_buffer[i] = features[i]

    print("Initial config:\n", dma.register_map)
    while run:
        try:
            dma.sendchannel.transfer(input_buffer)
            dma.recvchannel.transfer(output_buffer)
            dma.sendchannel.wait()
            dma.recvchannel.wait()

            action = output_buffer[0]

            if action == 0:
                return "logout"
            elif action == 1:
                return "shield"
            elif action == 2:
                return "reload"
            elif action == 3:
                return "grenade" 
            elif action == 4:
                return "none"
            
            run = False
        except RuntimeError as e:
            print(e)
            print("Error config: ", dma.register_map)


    # Call below statements once the buffers are no longer needed to free mem
    # del input_buffer
    # del output_buffer

        