# Smart Water Quality Monitoring System Using IoT and ML

This project provides a robust solution for monitoring water quality in real-time by combining IoT sensors (ESP32) and Machine Learning models (Random Forest Classifier).

## Hardware Setup

The physical setup includes an ESP32 microcontroller, breadboard, and water quality sensors submerged in the target water sample. Below is an image illustrating our hardware configuration:

![Hardware Setup](hardware_setup.jpg)

> **Note:** If the image is not loading, ensure that you have saved the provided setup image as `hardware_setup.jpg` in the root directory of this project.

## Features

- **IoT Integration**: Uses ESP32 to gather data from various sensors (pH, turbidity, temperature, dissolved oxygen, conductivity, nitrate).
- **Machine Learning**: A Random Forest Classifier trained on the `AquaAttributes` dataset is used to predict and classify the water quality status as `Good` or `Hazard`.
- **Live Prediction**: Integrates live sensor data from the ESP32 and runs it against the pre-trained ML model for instant classification.
- **Web Dashboard**: An integrated Django web application (`water_monitor`) to display real-time sensor metrics and predictions.

## Project Structure

- `water_quality_model.py`: Main ML pipeline script. It handles data loading, cleaning, feature selection, training, evaluation, and saving the model artifacts.
- `predict_sensor.py`: Script to make live predictions using the saved model artifacts.
- `test_model_accuracy.py`: Script to test the model's accuracy on the provided dataset.
- `water_monitor/`: Contains a Django web application used for dashboarding and monitoring the water quality data.
- `AquaAttributes.xlsx`: Dataset used for training the Random Forest Classifier.
- `model_outputs/`: Directory where the trained model (`water_quality_rf_model.joblib`), label encoder, feature names, and evaluation charts (confusion matrix, feature importance) are stored.

## Setup Instructions

1. **Install Requirements**: Ensure Python 3.8+ is installed. Run the following command to install required packages:
   ```bash
   pip install -r requirements.txt
   ```
2. **Train the Model**: Run the model training pipeline to generate the necessary model files:
   ```bash
   python water_quality_model.py
   ```
3. **Run Web Dashboard**: To view the web dashboard, navigate to the `water_monitor` directory and run the Django server:
   ```bash
   cd water_monitor
   python manage.py runserver
   ```

## Future Enhancements
- Expand the dataset for better model generalization.
- Integrate a cloud database for historical tracking of water quality.
- Add additional sensors for more granular parameter tracking.
