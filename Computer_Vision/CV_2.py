# -*- coding: utf-8 -*-
"""Untitled12.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1g19tSzmpBZWAaobKNbDgkWG9J-0lnnd3
"""

import torch
import torch.nn as nn
from torchvision import models
from flask import Flask, request, jsonify
import io
from PIL import Image
import onnx
import onnxruntime

app = Flask(__name__)

# Load the trained PyTorch model
model = models.resnet18(pretrained=True)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, NUM_CLASSES)
model.load_state_dict(torch.load('vegetable_classification_model.pth'))
model.eval()

# Convert the PyTorch model to ONNX format
dummy_input = torch.randn(1, 3, 224, 224)
onnx_path = 'vegetable_classification_model.onnx'
torch.onnx.export(model, dummy_input, onnx_path, opset_version=11)

# Optimize the ONNX model (Optional)
optimized_onnx_path = 'vegetable_classification_model_optimized.onnx'
onnx_model = onnx.load(onnx_path)
optimized_model = onnxruntime.optimizer.optimize(onnx_model)
onnx.save_model(optimized_model, optimized_onnx_path)

# Load the optimized ONNX model with ONNX Runtime
session = onnxruntime.InferenceSession(optimized_onnx_path)

# Define class labels (adjust according to your dataset)
class_labels = ['class1', 'class2', 'class3', ...]

# Define a route for the web app
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'})

    image_file = request.files['image']
    image = Image.open(io.BytesIO(image_file.read()))
    image = image.convert('RGB')
    image = image.resize((224, 224))  # Adjust to match model input size
    image = transforms.ToTensor()(image)
    image = image.unsqueeze(0)

    # Run inference with the ONNX model
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    outputs = session.run([output_name], {input_name: image.numpy()})
    probabilities = outputs[0][0]

    # Convert probabilities to class labels
    _, predicted_idx = torch.max(torch.tensor(probabilities), 0)
    predicted_label = class_labels[predicted_idx]

    return jsonify({'prediction': predicted_label})

# Run the Flask app
if __name__ == '__main__':
    app.run()