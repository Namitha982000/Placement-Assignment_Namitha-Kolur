# -*- coding: utf-8 -*-
"""CV_1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uodggiqyX7Yc0xL9QhtBhYI3VhA60btQ

# Question 1

## Import the necessary libraries:
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torch.utils.data.dataset import Dataset
from torch.utils.data.distributed import DistributedSampler
from torch.nn.parallel import DistributedDataParallel
import albumentations as A
from albumentations.pytorch import ToTensorV2
from torch.utils.tensorboard import SummaryWriter

"""## Define the vegetable dataset class:"""

class VegetableDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.images = os.listdir(root_dir)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image_path = os.path.join(self.root_dir, self.images[index])
        image = Image.open(image_path).convert("RGB")
        label = self.get_label_from_filename(self.images[index])
        if self.transform:
            image = self.transform(image)
        return image, label

    @staticmethod
    def get_label_from_filename(filename):
        return filename.split("_")[0]

"""## Define the CNN model:"""

class VegetableClassifier(nn.Module):
    def __init__(self, num_classes):
        super(VegetableClassifier, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(16 * 16 * 16, 256)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

"""## Define the distributed training function:"""

def train_distributed(rank, world_size, args):
    # Initialize distributed training
    torch.distributed.init_process_group(
        backend='nccl',
        init_method='env://'
    )
    torch.cuda.set_device(rank)

    # Define transformations for data augmentation
    train_transform = A.Compose([
        A.Resize(256, 256),
        A.RandomCrop(224, 224),
        A.HorizontalFlip(),
        A.Normalize(),
        ToTensor(),
    ])
    val_transform = A.Compose([
        A.Resize(256, 256),
        A.CenterCrop(224, 224),
        A.Normalize(),
        ToTensor(),
    ])

    # Create distributed data samplers
    train_sampler = DistributedSampler(VegetableDataset(args.train_dir, train_transform))
    val_sampler = DistributedSampler(VegetableDataset(args.val_dir, val_transform))

    # Create data loaders
    train_loader = DataLoader(
        VegetableDataset(args.train_dir, train_transform),
        batch_size=args.batch_size,
        sampler=train_sampler
    )
    val_loader = DataLoader(
        VegetableDataset(args.val_dir, val_transform),
        batch_size=args.batch_size,
        sampler=val_sampler
    )

    # Create model
    model = VegetableClassifier(args.num_classes)
    model = model.to(rank)
    model = DistributedDataParallel(model, device_ids=[rank])

    # Define loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # Initialize TensorBoard logging
    writer = SummaryWriter()

    # Start training
    for epoch in range(args.num_epochs):
        model.train()
        train_sampler.set_epoch(epoch)
        for i, (images, labels) in enumerate(train_loader):
            images = images.to(rank)
            labels = labels.to(rank)

            # Zero the gradients
            optimizer.zero_grad()

            # Forward pass
            outputs = model(images)
            loss = criterion(outputs, labels)

            # Backward pass and optimization
            loss.backward()
            optimizer.step()

            # Log loss to TensorBoard
            global_step = epoch * len(train_loader) + i
            writer.add_scalar('Loss/train', loss.item(), global_step)

        # Validate the model
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(rank)
                labels = labels.to(rank)

                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

                loss = criterion(outputs, labels)
                val_loss += loss.item()

        val_accuracy = correct / total
        val_loss /= len(val_loader)

        # Log validation accuracy and loss to TensorBoard
        writer.add_scalar('Accuracy/val', val_accuracy, epoch)
        writer.add_scalar('Loss/val', val_loss, epoch)

        # Print progress
        if rank == 0:
            print(f'Epoch [{epoch+1}/{args.num_epochs}], '
                  f'Validation Accuracy: {val_accuracy:.4f}, '
                  f'Validation Loss: {val_loss:.4f}')

    # Save the trained model
    if rank == 0:
        torch.save(model.module.state_dict(), args.save_path)

    # Clean up
    torch.distributed.destroy_process_group()


def main():
    # Set the arguments
    class Args:
        train_dir = "/path/to/train/directory"
        val_dir = "/path/to/validation/directory"
        batch_size = 32
        num_classes = 10
        num_epochs = 10
        lr = 0.001
        save_path = "model.pth"

    args = Args()

    # Initialize distributed training
    if torch.cuda.is_available():
        world_size = torch.cuda.device_count()
        torch.multiprocessing.spawn(
            train_distributed,
            args=(world_size, args),
            nprocs=world_size,
            join=True
        )
    else:
        print("GPU not available. Distributed training cannot be performed.")

if __name__ == '__main__':
    main()
