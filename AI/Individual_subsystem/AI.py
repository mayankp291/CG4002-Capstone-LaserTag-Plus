import numpy as np
import tensorflow as tf
import os

from sklearn.model_selection import train_test_split
from sklearn import metrics
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew
from scipy.fftpack import fft
from sklearn.preprocessing import minmax_scale

# INPUTS = 792 # 128 captures (for one sensor reading) * 6 sensor reading types + 4 extracted features * 6 sensor reading types --> only talking about the width, not the length of matrices

NEURONS_HIDDEN_LAYER = [56]
DROPOUT = 0.40
NUM_FEATURES = 4
INPUTS = NUM_FEATURES * 6 #  4 extracted features * 6 sensor reading types 
DATA_LABELS = ["WALKING", "WALKING_UPSTAIRS", "WALKING_DOWNSTAIRS", "SITTING", "STANDING", "LAYING"]
OUTPUTS = len(DATA_LABELS)
EPOCHS = 50
PRECISION_TRAIN_DATA = 10
PRECISION_TEST_DATA = 8
PRECISION_WEIGHTS = 9


def read_raw_data(path_to_dataset):
    array = []
    with open(path_to_dataset, 'r') as text_file:
        lines = text_file.readlines()
        for line in lines:
            array.append(line.strip().replace("  ", " ").split())
    
    return array


def extract_features(*argsv):

    # -1 in reshape means let numpy figure out that particular dimension. 
    # NOTE: doing reshape(-1, -1) doesn't work, only one value can have -1

    mean_acc_x = np.mean(argsv[0], axis=1).reshape(-1,1)
    mean_acc_y = np.mean(argsv[1], axis=1).reshape(-1,1)
    mean_acc_z = np.mean(argsv[2], axis=1).reshape(-1,1)
    mean_gyro_x = np.mean(argsv[3], axis=1).reshape(-1,1)
    mean_gyro_y = np.mean(argsv[4], axis=1).reshape(-1,1)
    mean_gyro_z = np.mean(argsv[5], axis=1).reshape(-1,1)

    sd_acc_x = np.std(argsv[0], axis=1).reshape(-1,1) 
    sd_acc_y = np.std(argsv[1], axis=1).reshape(-1,1) 
    sd_acc_z = np.std(argsv[2], axis=1).reshape(-1,1) 
    sd_gyro_x = np.std(argsv[3], axis=1).reshape(-1,1)
    sd_gyro_y = np.std(argsv[4], axis=1).reshape(-1,1)
    sd_gyro_z = np.std(argsv[5], axis=1).reshape(-1,1)

    max_acc_x = np.amax(argsv[0], axis=1).reshape(-1,1)
    max_acc_y = np.amax(argsv[1], axis=1).reshape(-1,1)
    max_acc_z = np.amax(argsv[2], axis=1).reshape(-1,1)
    max_gyro_x = np.amax(argsv[3], axis=1).reshape(-1,1)
    max_gyro_y = np.amax(argsv[4], axis=1).reshape(-1,1)
    max_gyro_z = np.amax(argsv[5], axis=1).reshape(-1,1)

    min_acc_x = np.amin(argsv[0], axis=1).reshape(-1,1)
    min_acc_y = np.amin(argsv[1], axis=1).reshape(-1,1)
    min_acc_z = np.amin(argsv[2], axis=1).reshape(-1,1)
    min_gyro_x = np.amin(argsv[3], axis=1).reshape(-1,1)
    min_gyro_y = np.amin(argsv[4], axis=1).reshape(-1,1)
    min_gyro_z = np.amin(argsv[5], axis=1).reshape(-1,1)

    # rms_acc_x = np.reshape((np.sqrt(np.mean(argsv[0]**2, axis=1))), (-1, 1))
    # rms_acc_y = np.reshape((np.sqrt(np.mean(argsv[1]**2, axis=1))), (-1, 1))
    # rms_acc_z = np.reshape((np.sqrt(np.mean(argsv[2]**2, axis=1))), (-1, 1))
    # rms_gyro_x = np.reshape((np.sqrt(np.mean(argsv[3]**2, axis=1))), (-1, 1))
    # rms_gyro_y = np.reshape((np.sqrt(np.mean(argsv[4]**2, axis=1))), (-1, 1))
    # rms_gyro_z = np.reshape((np.sqrt(np.mean(argsv[5]**2, axis=1))), (-1, 1))

    # skew_acc_x = np.reshape(skew(argsv[0], axis=1), (-1, 1))
    # skew_acc_y = np.reshape(skew(argsv[1], axis=1), (-1, 1))
    # skew_acc_z = np.reshape(skew(argsv[2], axis=1), (-1, 1))
    # skew_gyro_x = np.reshape(skew(argsv[3], axis=1), (-1, 1))
    # skew_gyro_y = np.reshape(skew(argsv[4], axis=1), (-1, 1))
    # skew_gyro_z = np.reshape(skew(argsv[5], axis=1), (-1, 1))

    # Convert to frequency domain
    # signal_acc_x = fft(argsv[0], axis=1)
    # signal_acc_y = fft(argsv[1], axis=1)
    # signal_acc_z = fft(argsv[2], axis=1)
    # signal_gyro_x = fft(argsv[3], axis=1)
    # signal_gyro_y = fft(argsv[4], axis=1)
    # signal_gyro_z = fft(argsv[5], axis=1)

    # mag_acc_x = np.reshape((np.amax(np.abs(fft(argsv[0], axis=1)), axis=1)), (-1, 1))
    # mag_acc_y = np.reshape((np.amax(np.abs(fft(argsv[1], axis=1)), axis=1)), (-1, 1))
    # mag_acc_z = np.reshape((np.amax(np.abs(fft(argsv[2], axis=1)), axis=1)), (-1, 1))
    # mag_gyro_x = np.reshape((np.amax(np.abs(fft(argsv[3], axis=1)), axis=1)), (-1, 1))
    # mag_gyro_y = np.reshape((np.amax(np.abs(fft(argsv[4], axis=1)), axis=1)), (-1, 1))
    # mag_gyro_z = np.reshape((np.amax(np.abs(fft(argsv[5], axis=1)), axis=1)), (-1, 1))


    # phase_acc_x = np.reshape((np.amax(np.angle(fft(argsv[0], axis=1)), axis=1)), (-1, 1))
    # phase_acc_y = np.reshape((np.amax(np.angle(fft(argsv[1], axis=1)), axis=1)), (-1, 1))
    # phase_acc_z = np.reshape((np.amax(np.angle(fft(argsv[2], axis=1)), axis=1)), (-1, 1))
    # phase_gyro_x = np.reshape((np.amax(np.angle(fft(argsv[3], axis=1)), axis=1)), (-1, 1))
    # phase_gyro_y = np.reshape((np.amax(np.angle(fft(argsv[4], axis=1)), axis=1)), (-1, 1))
    # phase_gyro_z = np.reshape((np.amax(np.angle(fft(argsv[5], axis=1)), axis=1)), (-1, 1))

    # Concatenating operation
    # axis = 1 implies that it is being done column-wise, e.g. [1, 1] concatenate with [3, 5] gives [1, 1, 3, 5]
    # axis = 0 implies row-wise operation, e.g. [1, 1] with [3, 5] gives [[1, 1],
    #                                                                     [3, 5]]
    return np.concatenate((mean_acc_x, mean_acc_y, mean_acc_z, mean_gyro_x, mean_gyro_y, mean_gyro_z,         sd_acc_x, sd_acc_y, sd_acc_z, sd_gyro_x, sd_gyro_y, sd_gyro_z, 
    max_acc_x, max_acc_y, max_acc_z, max_gyro_x, max_gyro_y, max_gyro_z,
    min_acc_x, min_acc_y, min_acc_z, min_gyro_x, min_gyro_y, min_gyro_z), axis=1)


def get_data_labels(data_type):
    labels = []

    with open(f"Dataset/{data_type}/y_{data_type}.txt", "r") as text_file:
        lines = text_file.readlines()
        for line in lines:
            label = int(line.strip())

            if label == 1:
                labels.append([1, 0, 0, 0, 0, 0])
            elif label == 2:
                labels.append([0, 1, 0, 0, 0, 0])
            elif label == 3:
                labels.append([0, 0, 1, 0, 0, 0])
            elif label == 4:
                labels.append([0, 0, 0, 1, 0, 0])
            elif label == 5:
                labels.append([0, 0, 0, 0, 1, 0])
            else:
                labels.append([0, 0, 0, 0, 0, 1])

    return labels


def get_thresholds(*argsv):
    
    if argsv[6] == "train":
        # Obtain thresholds of acc and gyro readings for training data
        max_neg_acc_x = np.max(argsv[0][argsv[0] < 0])
        min_pos_acc_x = np.min(argsv[0][argsv[0] > 0])

        max_neg_acc_y = np.max(argsv[1][argsv[1] < 0])
        min_pos_acc_y = np.min(argsv[1][argsv[1] > 0])

        max_neg_acc_z = np.max(argsv[2][argsv[2] < 0])
        min_pos_acc_z = np.min(argsv[2][argsv[2] > 0])

        max_neg_gyro_x = np.max(argsv[3][argsv[3] < 0])
        min_pos_gyro_x = np.min(argsv[3][argsv[3] > 0])

        max_neg_gyro_y = np.max(argsv[4][argsv[4] < 0])
        min_pos_gyro_y = np.min(argsv[4][argsv[4] > 0])

        max_neg_gyro_z = np.max(argsv[5][argsv[5] < 0])
        min_pos_gyro_z = np.min(argsv[5][argsv[5] > 0])

        thresholds = np.array([max_neg_acc_x, min_pos_acc_x, 
                            max_neg_acc_y, min_pos_acc_y, 
                            max_neg_acc_z, min_pos_acc_z,
                            max_neg_gyro_x, min_pos_gyro_x,
                            max_neg_gyro_y, min_pos_gyro_y,
                            max_neg_gyro_z, min_pos_gyro_z])
    
        np.savetxt("threshold.txt", [thresholds], fmt=f"%.{PRECISION_TRAIN_DATA}f", delimiter=", ")


def normalise(matrix, data_type="train"):
    
    if data_type == "train":
        print(matrix[0])
        print(minmax_scale(matrix.T).T[0])
        print(np.amax(matrix[0]), np.amin(matrix[0]))

    return minmax_scale(matrix.T).T  


def load_data(data_paths, data_type):
    
    print(f"\nLoading raw {data_type}ing data...")
    
    body_acc_x, body_acc_y, body_acc_z, body_gyro_x, body_gyro_y, body_gyro_z = (
        normalise(np.array(read_raw_data(data_paths[i])).astype(np.float32)) for i in range(len(data_paths)))

    print(f"Raw {data_type}ing data loaded! \nLoading {data_type}ing labels...")

    labels = get_data_labels(data_type)

    print(f"{data_type.capitalize()}ing labels loaded!\nExtracting features...")

    # get_thresholds(body_acc_x, body_acc_y, body_acc_z, body_gyro_x, body_gyro_y, body_gyro_z, data_type)

    extracted_features = extract_features(body_acc_x, body_acc_y, body_acc_z, body_gyro_x, body_gyro_y, body_gyro_z, data_type) 

    print(f"Extracted features!\n{data_type.capitalize()}ing data is ready to be used!\n")

    return extracted_features, np.array(labels).astype(np.float32)


def get_data_paths(path_type):
        base_path = f"Dataset/{path_type}/Inertial Signals/"
        return [f"{base_path}body_acc_x_{path_type}.txt", f"{base_path}body_acc_y_{path_type}.txt", 
                f"{base_path}body_acc_z_{path_type}.txt", f"{base_path}body_gyro_x_{path_type}.txt", 
                f"{base_path}body_gyro_y_{path_type}.txt", f"{base_path}body_gyro_z_{path_type}.txt"]


def get_model():
    model = tf.keras.models.Sequential()

    model.add(tf.keras.layers.Dense(NEURONS_HIDDEN_LAYER[0], input_shape=(INPUTS,), activation="relu"))
    model.add(tf.keras.layers.Dropout(DROPOUT))
    
    i = 1
    while (i < len(NEURONS_HIDDEN_LAYER)):
        model.add(tf.keras.layers.Dense(NEURONS_HIDDEN_LAYER[i], activation="relu"))
        model.add(tf.keras.layers.Dropout(DROPOUT))
        i += 1
    

    model.add(tf.keras.layers.Dense(OUTPUTS, activation="softmax"))

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model

def save_raw_weights_to_file(model, file_name):
    
    if os.path.exists(file_name):
        os.remove(file_name)
    
    with open(file_name, "a") as params_file:
        for index, layer in enumerate(model.layers):
            if len(layer.get_weights()) > 0:
                print(f"layer {index}\n", layer.get_weights())
                for count, ele in enumerate(["weights", "biases"]):
                    params_file.write(f"\n\n\nlayer {index} - {ele}\n\n")
                    weights_content = np.transpose(layer.get_weights()[count])
                    params_file.write(str(weights_content.shape) + "\n\n")
                    np.savetxt(params_file, weights_content, fmt=f"%.{PRECISION_WEIGHTS}f", delimiter=", ")
                    print(layer.get_weights()[count].shape)


def is_array_correct(array_content, indexes):
    total_length = 0
    if not indexes[0]:
        total_length = int(indexes[1])
    elif not indexes[1]:
        total_length = int(indexes[0])
    else:
        total_length = int(indexes[0]) * int(indexes[1])
    
    return total_length == len(array_content.split(","))

def convert_to_c(file_name):

    converted_content = ""
    with open(file_name, 'r') as params_file:
        lines = params_file.readlines()
        curr_array_len = actual_array_len = 0
        array_content  = ""
        for line in lines:
            if not line or line.isspace() or line.startswith("layer"):
                converted_content += line
                continue
            if line.startswith("("):
                indexes = line.replace("(", "").replace(")", "").strip().split(",")
                actual_array_len = int(indexes[0].strip())
                curr_array_len = 0
                array_content = ""
                continue
            
            # if line.count(",") > 1:
            #     if curr_array_len == (actual_array_len - 1):
            #         array_content += ("{" + line.strip() + "}\n")
            #         converted_content += array_content
            #     else:
            #         array_content += ("{" + line.strip() + "},\n")
            # else:
            #     if curr_array_len == 0:
            #         array_content += ("{" + line.strip() + ", \n")
            #     elif curr_array_len == (actual_array_len - 1):
            #         array_content += (line.strip() + "}\n")
            #         assert is_array_correct(array_content, indexes)
            #         converted_content += array_content
            #     else:
            #         array_content += (line.strip() + ", ")

            if curr_array_len == 0:
                    array_content += ("{" + line.strip() + ", \n")
            elif curr_array_len == (actual_array_len - 1):
                array_content += (line.strip() + "}\n")
                assert is_array_correct(array_content, indexes)
                converted_content += array_content
            else:
                array_content += (line.strip() + ", ")

            curr_array_len += 1

    with open(file_name, "w") as params_file:
        params_file.write(converted_content)


def extract_params(model, file_name):

    save_raw_weights_to_file(model, file_name)
    convert_to_c(file_name)
    

def save_raw_test_data_to_file(testing_dataset, testing_data_labels, file_name):
    
    if os.path.exists(file_name):
        os.remove(file_name)

    with open(file_name, "a") as test_file:
        print("\n\nTesting Data params:\n\n" +
              f"{testing_dataset.shape} {testing_data_labels.shape}")
        test_file.write(f"{testing_dataset.shape}\n")
        np.savetxt(test_file, (np.array(testing_dataset) * pow(10, PRECISION_TEST_DATA)), fmt="%d", delimiter=", ")
        test_file.write("\n\n\n\n\n")

        test_file.write(f"{testing_data_labels.shape}\n")
        np.savetxt(test_file, testing_data_labels, fmt="%d", delimiter=", ")


def save_testing_data(testing_dataset, testing_data_labels, file_name):
    
    save_raw_test_data_to_file(testing_dataset, testing_data_labels, file_name)
    convert_to_c(file_name)


def main():

    model = get_model()
    print(model.summary())

    training_data_paths = get_data_paths("train")
    testing_data_paths = get_data_paths("test")
    training_dataset, training_data_labels = load_data(training_data_paths, "train")
    testing_dataset, testing_data_labels = load_data(testing_data_paths, "test")
    print(testing_dataset.shape, testing_data_labels.shape)

    # Train the neural network model
    model.fit(training_dataset, training_data_labels, epochs=EPOCHS)

    # Evaluate how well model performs
    model.evaluate(testing_dataset, testing_data_labels, verbose=2)

    # Create confusion matrix
    predicted_labels = model.predict(testing_dataset)
    predicted_labels = tf.argmax(predicted_labels, axis=1)
    testing_data_labels = tf.argmax(testing_data_labels, axis=1 )
    confusion_matrix = metrics.confusion_matrix(testing_data_labels, predicted_labels)
    
    # Print confusion matrix in terminal
    print(confusion_matrix)

    # Print classification report with all values
    print(metrics.classification_report(testing_data_labels, predicted_labels))
    
    # Print matrix in separate window
    sns.heatmap(confusion_matrix, cmap="Blues", annot=True, 
                cbar_kws={"orientation":"vertical", "label": "Number of readings"},
                xticklabels=DATA_LABELS, yticklabels=DATA_LABELS)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    
    # Comment/Uncomment out to remove/restore the heat map 
    plt.show()

    # Extract weights and biases to text file
    extract_params(model, "params.txt")

    # Print testing dataset to text file
    save_testing_data(testing_dataset, testing_data_labels, "testing_data.txt")


if __name__ == "__main__":
    main()