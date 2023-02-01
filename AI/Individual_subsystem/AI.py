import numpy as np
import tensorflow as tf
import os

from sklearn.model_selection import train_test_split
from sklearn import metrics
import matplotlib.pyplot as plt
import seaborn as sns

NEURONS_HIDDEN_LAYER = [192, 256]
DROPOUT = 0.40
INPUTS = 792 # 128 captures (for one sensor reading) * 6 sensor reading types + 4 extracted features * 6 sensor reading types --> only talking about the width, not the length of matrices
DATA_LABELS = ["WALKING", "WALKING_UPSTAIRS", "WALKING_DOWNSTAIRS", "SITTING", "STANDING", "LAYING"]
OUTPUTS = len(DATA_LABELS)
EPOCHS = 30


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


    # Concatenating operation
    # axis = 1 implies that it is being done column-wise, e.g. [1, 1] concatenate with [3, 5] gives [1, 1, 3, 5]
    # axis = 0 implies row-wise operation, e.g. [1, 1] with [3, 5] gives [[1, 1],
    #                                                                     [3, 5]]
    return np.concatenate((mean_acc_x, mean_acc_y, mean_acc_z, mean_gyro_x, mean_gyro_y, mean_gyro_z, sd_acc_x, sd_acc_y, sd_acc_z, sd_gyro_x, sd_gyro_y, sd_gyro_z, max_acc_x, max_acc_y, max_acc_z, max_gyro_x, max_gyro_y, max_gyro_z, min_acc_x, min_acc_y, min_acc_z, min_gyro_x, min_gyro_y, min_gyro_z), axis=1)


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


def load_data(data_paths, data_type):
    
    print(f"\nLoading raw {data_type}ing data...")
    
    body_acc_x, body_acc_y, body_acc_z, body_gyro_x, body_gyro_y, body_gyro_z = (
        np.array(read_raw_data(data_paths[i])).astype(np.float32) for i in range(len(data_paths)))

    print(f"Raw {data_type}ing data loaded! \nLoading {data_type}ing labels...")

    labels = get_data_labels(data_type)

    print(f"{data_type.capitalize()}ing labels loaded!\nExtracting features...")

    extracted_features = extract_features(body_acc_x, body_acc_y, body_acc_z, body_gyro_x, body_gyro_y, body_gyro_z)

    print(f"Extracted features!\n{data_type.capitalize()}ing data is ready to be used!\n")


    return np.column_stack((body_acc_x, body_acc_y, body_acc_z, body_gyro_x, body_gyro_y, body_gyro_z, extracted_features)), np.array(labels).astype(np.float32)


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

def save_raw_to_file(model, file_name):
    
    if os.path.exists(file_name):
        os.remove(file_name)
    
    with open(file_name, "a") as hyperparams_file:
        for index, layer in enumerate(model.layers):
            if len(layer.get_weights()) > 0:
                print(f"layer {index}\n", layer.get_weights())
                for count, ele in enumerate(["weights", "biases"]):
                    hyperparams_file.write(f"\n\n\nlayer {index} - {ele}\n\n")
                    np.savetxt(hyperparams_file, np.transpose(layer.get_weights()[count], fmt="%.10f", delimiter=", ")
                    print(layer.get_weights()[count].shape)


def convert_to_c(file_name):

    converted_content = ""
    with open(file_name, 'r') as hyperparams_file:
        lines = hyperparams_file.readlines()
        for index, line in enumerate(lines):
            if not line or line.isspace() or line.startswith("layer"):
                converted_content += (line + "\n")
                continue
            converted_content += ("{" + line.strip() + "},\n") if (index < (len(lines) - 1)) else ("{" + line.strip() + "}\n")

    with open(file_name, "w") as hyperparams_file:
        hyperparams_file.write(converted_content)


def extract_params(model, file_name):

    save_raw_to_file(model, file_name)
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
    # plt.show()

    # Extract weights and biases to text file
    extract_params(model, "hyperparams.txt")



if __name__ == "__main__":
    main()