import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms
from torch.utils.data import DataLoader
from model import CowSonogramCNN, CLASSES
from dataset_loader import CowSonogramDataset
import os

def train_model(data_dir, epochs=50, batch_size=32, lr=0.001):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on {device}...")
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    if not os.path.exists(data_dir):
        print(f"Dataset directory '{data_dir}' not found.")
        return

    try:
        dataset = CowSonogramDataset(data_dir, transform=transform)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        print(f"Loaded {len(dataset)} images for multi-task training.")
    except Exception as e:
        print(f"Could not load dataset from {data_dir}.")
        print(e)
        return
        
    model = CowSonogramCNN(num_classes=len(CLASSES)).to(device)
    
    criterion_class = nn.CrossEntropyLoss()
    criterion_yield = nn.MSELoss()
    
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        running_class_loss = 0.0
        running_yield_loss = 0.0
        
        for i, (inputs, class_labels, yield_labels) in enumerate(dataloader):
            inputs = inputs.to(device)
            class_labels = class_labels.to(device)
            yield_labels = yield_labels.to(device)
            
            optimizer.zero_grad()
            class_logits, yield_preds = model(inputs)
            
            loss_c = criterion_class(class_logits, class_labels)
            # Alpha/beta can be tuned, but we use 1.0/1.0 initially
            loss_y = criterion_yield(yield_preds, yield_labels)
            
            # Since MSE loss on ~30 yield might be large (like 100), we scale it down slightly
            combined_loss = loss_c + (0.1 * loss_y) 
            
            combined_loss.backward()
            optimizer.step()
            
            running_loss += combined_loss.item()
            running_class_loss += loss_c.item()
            running_yield_loss += loss_y.item()
            
        avg_loss = running_loss / len(dataloader)
        avg_c = running_class_loss / len(dataloader)
        avg_y = running_yield_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{epochs} - Combined Loss: {avg_loss:.4f} (Class: {avg_c:.4f}, Yield(MSE): {avg_y:.4f})")
        
    torch.save(model.state_dict(), 'cow_model.pth')
    print("Training complete. Model saved to cow_model.pth")

if __name__ == "__main__":
    train_model(data_dir='dataset/train')

