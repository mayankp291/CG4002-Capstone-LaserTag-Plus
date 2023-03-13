import numpy as np
import tensorflow as tf
from scipy.stats import skew
from scipy.fftpack import fft

arr1 = arr2 = arr3 = arr4 = arr5 = arr6 = []
model = tf.keras.models.load_model('my_model.h5')

with open("test_AI.txt", "r") as txt_file: 
    lines = txt_file.readlines()
    for count, line in enumerate(lines):
        if count == 0:
            arr1 = line.split(",")
        elif count == 1:
            arr2 = line.split(",")
        elif count == 2:
            arr3 = line.split(",")
        elif count == 3:
            arr4 = line.split(",")
        elif count == 4:
            arr5 = line.split(",")
        elif count == 5:
            arr6 = line.split(",")


def extract_features(input):
    
    mean_acc_x = np.mean(input[0]).reshape(-1,1)
    mean_acc_y = np.mean(input[1]).reshape(-1,1)
    mean_acc_z = np.mean(input[2]).reshape(-1,1)
    mean_gyro_x = np.mean(input[3]).reshape(-1,1)
    mean_gyro_y = np.mean(input[4]).reshape(-1,1)
    mean_gyro_z = np.mean(input[5]).reshape(-1,1)


    sd_acc_x = np.std(input[0]).reshape(-1,1) 
    sd_acc_y = np.std(input[1]).reshape(-1,1) 
    sd_acc_z = np.std(input[2]).reshape(-1,1) 
    sd_gyro_x = np.std(input[3]).reshape(-1,1)
    sd_gyro_y = np.std(input[4]).reshape(-1,1) 
    sd_gyro_z = np.std(input[5]).reshape(-1,1) 

    max_acc_x = np.amax(input[0]).reshape(-1,1)
    max_acc_y = np.amax(input[1]).reshape(-1,1)
    max_acc_z = np.amax(input[2]).reshape(-1,1)
    max_gyro_x = np.amax(input[3]).reshape(-1,1)
    max_gyro_y = np.amax(input[4]).reshape(-1,1)
    max_gyro_z = np.amax(input[5]).reshape(-1,1)

    min_acc_x = np.amin(input[0]).reshape(-1,1)
    min_acc_y = np.amin(input[1]).reshape(-1,1)
    min_acc_z = np.amin(input[2]).reshape(-1,1)
    min_gyro_x = np.amin(input[3]).reshape(-1,1)
    min_gyro_y = np.amin(input[4]).reshape(-1,1)
    min_gyro_z = np.amin(input[5]).reshape(-1,1)

    rms_acc_x = np.reshape((np.sqrt(np.mean(input[0]**2))), (-1, 1))
    rms_acc_y = np.reshape((np.sqrt(np.mean(input[1]**2))), (-1, 1))
    rms_acc_z = np.reshape((np.sqrt(np.mean(input[2]**2))), (-1, 1))
    rms_gyro_x = np.reshape((np.sqrt(np.mean(input[3]**2))), (-1, 1))
    rms_gyro_y = np.reshape((np.sqrt(np.mean(input[4]**2))), (-1, 1))
    rms_gyro_z = np.reshape((np.sqrt(np.mean(input[5]**2))), (-1, 1))

    skew_acc_x = np.reshape(skew(input[0]), (-1, 1))
    skew_acc_y = np.reshape(skew(input[1]), (-1, 1))
    skew_acc_z = np.reshape(skew(input[2]), (-1, 1))
    skew_gyro_x = np.reshape(skew(input[3]), (-1, 1))
    skew_gyro_y = np.reshape(skew(input[4]), (-1, 1))
    skew_gyro_z = np.reshape(skew(input[5]), (-1, 1))

    # # Convert to frequency domain
    # signal_acc_x = fft(input[0], axis=1)
    # signal_acc_y = fft(input[1], axis=1)
    # signal_acc_z = fft(input[2], axis=1)
    # signal_gyro_x = fft(input[3], axis=1)
    # signal_gyro_y = fft(input[4], axis=1)
    # signal_gyro_z = fft(input[5], axis=1)

    mag_acc_x = np.reshape(np.amax(np.abs(fft(input[0]))), (-1, 1))
    mag_acc_y = np.reshape(np.amax(np.abs(fft(input[1]))), (-1, 1))
    mag_acc_z = np.reshape(np.amax(np.abs(fft(input[2]))), (-1, 1))
    mag_gyro_x = np.reshape(np.amax(np.abs(fft(input[3]))), (-1, 1))
    mag_gyro_y = np.reshape(np.amax(np.abs(fft(input[4]))), (-1, 1))
    mag_gyro_z = np.reshape(np.amax(np.abs(fft(input[5]))), (-1, 1))


    phase_acc_x = np.reshape(np.amax(np.angle(fft(input[0]))), (-1, 1))
    phase_acc_y = np.reshape(np.amax(np.angle(fft(input[1]))), (-1, 1))
    phase_acc_z = np.reshape(np.amax(np.angle(fft(input[2]))), (-1, 1))
    phase_gyro_x = np.reshape(np.amax(np.angle(fft(input[3]))), (-1, 1))
    phase_gyro_y = np.reshape(np.amax(np.angle(fft(input[4]))), (-1, 1))
    phase_gyro_z = np.reshape(np.amax(np.angle(fft(input[5]))), (-1, 1))

    return np.concatenate((mean_acc_x, mean_acc_y, mean_acc_z, mean_gyro_x, mean_gyro_y, mean_gyro_z,      sd_acc_x, sd_acc_y, sd_acc_z, sd_gyro_x, sd_gyro_y, sd_gyro_z, 
            max_acc_x, max_acc_y, max_acc_z, max_gyro_x, max_gyro_y, max_gyro_z,
            min_acc_x, min_acc_y, min_acc_z, min_gyro_x, min_gyro_y, min_gyro_z, 
            rms_acc_x, rms_acc_y, rms_acc_z, rms_gyro_x, rms_gyro_y, rms_gyro_z, 
            skew_acc_x, skew_acc_y, skew_acc_z, skew_gyro_x, skew_gyro_y, skew_gyro_z,
            mag_acc_x, mag_acc_y, mag_acc_z, mag_gyro_x, mag_gyro_y, mag_gyro_z,
            phase_acc_x, phase_acc_y, phase_acc_z, phase_gyro_x, phase_gyro_y, phase_gyro_z), axis=1).astype(np.int32)

raw_data = np.array([arr1, arr2, arr3, arr4, arr5, arr6]).astype(np.float32)

features = extract_features(raw_data)
predictions = model.predict(features)

# Print the predicted class
predicted_class = np.argmax(predictions[0])
mapping = {0:'LOGOUT', 1:'SHIELD', 2:'RELOAD', 3:'GRENADE', 4:'IDLE'}
print('Predicted class:', predicted_class, mapping[predicted_class])

