import csv
import tensorflow as tf

from sklearn.model_selection import train_test_split

NEURONS_HIDDEN_LAYER = [128,]
INPUTS = 6
OUTPUTS = 5
EPOCHS = 20

def load_training_data():
    return

def load_testing_data():
    return

def get_model():
    model = tf.keras.models.Sequential()

    model.add(tf.keras.layers.Dense(NEURONS_HIDDEN_LAYER[0], input_shape=(INPUTS,), activation="relu"))
    model.add(tf.keras.layers.Dropout(0.3))
    
    i = 1
    while (i < len(NEURONS_HIDDEN_LAYER)):
        model.add(tf.keras.layers.Dense(NEURONS_HIDDEN_LAYER[0], activation="relu"))
        model.add(tf.keras.layers.Dropout(0.3))
        i += 1
    

    model.add(tf.keras.layers.Dense(OUTPUTS, activation="softmax"))

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model

def main():

    model = get_model()
    training_dataset, training_data_label = load_training_data()
    testing_dataset, testing_data_label = load_testing_data()


    # Train the neural network model
    model.fit(training_dataset, training_data_label, epochs=EPOCHS)

    # Evaluate how well model performs
    model.evaluate(testing_dataset, testing_data_label, verbose=2)


if __name__ == "__main__":
    main()