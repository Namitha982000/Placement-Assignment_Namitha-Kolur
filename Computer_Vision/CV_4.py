# -*- coding: utf-8 -*-
"""CV_4.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UX4sPygaKxZABdhOkH5Z3TmaOzEMePz3

# Question 4
"""

from google.colab import drive
drive.mount('/content/drive')

# Import necessary libraries
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.models import vgg16

# Define the YOLO V7 model
class YOLOv7(nn.Module):
    def __init__(self, num_classes):
        super(YOLOv7, self).__init__()
        # Define your model architecture here
        
    def forward(self, x):
        # Implement the forward pass of your model
        
# Define the transformations to be applied to the images
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])

# Set the path to the dataset folder
    dataset_path = '/content/drive/MyDrive/Product Object Detection.v1i.yolov7pytorch'

    # Define the dataset loaders
    train_dataset = ImageFolder(root=dataset_path + '/train', transform=transforms)
    val_dataset = ImageFolder(root=dataset_path + '/valid', transform=transforms)
    test_dataset = ImageFolder(root=dataset_path + '/test', transform=transforms)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=4)

    # Initialize the YOLO V7 model
    model = YOLOv7(num_classes=102)

    # Define the loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    for epoch in range(10):
        train_loss = 0.0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * images.size(0)
        
        train_loss /= len(train_loader.dataset)
        print(f"Epoch {epoch+1} - Train Loss: {train_loss:.4f}")
        
        # Validation loop
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * images.size(0)
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == labels).sum().item()
                total += labels.size(0)
        
        val_loss /= len(val_loader.dataset)
        val_accuracy = correct / total * 100
        print(f"Epoch {epoch+1} - Val Loss: {val_loss:.4f} - Val Accuracy: {val_accuracy:.2f}%")

# Test the model
model.eval()
test_loss = 0.0
correct = 0
total = 0

with torch.no_grad():
    for images, labels in test_loader:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        test_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

test_loss /= len(test_loader.dataset)
test_accuracy = correct / total * 100
print(f"Test Loss: {test_loss:.4f} - Test Accuracy: {test_accuracy:.2f}%")
