# -*- coding: utf-8 -*-
"""CV_3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1c08TVlByDlMEC5lOuzy9eRJ3Wj-HiqS6

# Question 3
"""

import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

# Step 1: Scraping Images
# Define the target e-commerce websites and their URLs
websites = [
    {
        "name": "Website 1",
        "url": "https://www.amazon.in/"
    },
    {
        "name": "Website 2",
        "url": "https://www.amazon.in/"
    }
]

# Define the directory to store the downloaded images
download_dir = r"F:\DOCUMENTS\iNeuron_Assignment_NAM\FINAL_ASSIGNMENT\images"

# Create the download directory if it doesn't exist
os.makedirs(download_dir, exist_ok=True)

# Scraping function
def scrape_images(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    image_urls = []
    for img in soup.find_all("img"):
        image_url = img.get("src")
        if image_url and image_url.startswith("http"):
            image_urls.append(image_url)
    return image_urls

# Iterate over the websites and scrape images
for website in websites:
    print(f"Scraping images from {website['name']}")
    urls = scrape_images(website["url"])
    for i, url in enumerate(urls):
        response = requests.get(url)
        image_path = os.path.join(download_dir, f"{website['name']}_image_{i}.jpg")
        with open(image_path, "wb") as f:
            f.write(response.content)

# Step 2: Creating Categories
# Define the categories of different product classes
categories = ["category1", "category2", "category3", "category4"]

# Step 3: Dataset Preparation
class CustomDataset(Dataset):
    def __init__(self, root_dir, categories, transform=None):
        self.root_dir = root_dir
        self.categories = categories
        self.transform = transform

    def __len__(self):
        return len(os.listdir(self.root_dir))

    def __getitem__(self, idx):
        image_name = os.listdir(self.root_dir)[idx]
        image_path = os.path.join(self.root_dir, image_name)
        image = Image.open(image_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        category = int(image_name.split("_")[1])  # Extract the category from the image name
        return image, category

# Define the image transformations (resize, normalize, etc.)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
])

# Create the dataset
dataset = CustomDataset(download_dir, categories, transform=transform)

# Split the dataset into training and validation sets
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

# Step 4: Designing Custom Deep Learning Model
class CustomModel(nn.Module):
    def __init__(self, num_classes):
        super(CustomModel, self).__init__()
        # Define your custom model architecture
        self.conv1 = nn.Conv2d(3, 16, 3, 1, 1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, 3, 1, 1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 56 * 56, 128)
        self.relu3 = nn.ReLU()
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.conv1(x)
        x = self.relu1(x)
        x = self.pool1(x)
        x = self.conv2(x)
        x = self.relu2(x)
        x = self.pool2(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.relu3(x)
        x = self.fc2(x)
        return x

# Create an instance of the custom model
model = CustomModel(num_classes=len(categories))

# Step 5: Training the Model
# Define the loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Set the device for training (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Define the dataloaders
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32)

# Training loop
num_epochs = 10
for epoch in range(num_epochs):
    running_loss = 0.0
    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    # Print the average loss for the epoch
    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss / len(train_loader)}")

# Step 6: Model Inference
# Function to classify an input image
def classify_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)
    image = image.to(device)

    model.eval()
    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs.data, 1)

    category = categories[predicted.item()]
    return category

# Example usage
image_path = "path/to/input_image.jpg"
predicted_category = classify_image(image_path)
print(f"Predicted category: {predicted_category}")
