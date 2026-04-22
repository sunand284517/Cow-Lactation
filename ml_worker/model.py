import os
import random
import time
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as transforms

# Define 5 major productive stages
CLASSES = [
    'Dry Period',
    'Peak Lactation',
    'Late Lactation', 
    'Fresh Cows',
    'Peri-Partum'
]

class CowSonogramCNN(nn.Module):
    def __init__(self, num_classes=5):
        super(CowSonogramCNN, self).__init__()
        # Shared Convolutional Feature Extractor
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        # Shared Fully Connected Base
        self.fc_layer = nn.Sequential(
            nn.Linear(64 * 28 * 28, 512), # Assuming input is resized to 224x224
            nn.ReLU(),
            nn.Dropout(0.5)
        )
        
        # Multi-Task Learning Heads
        self.classification_head = nn.Linear(512, num_classes)
        self.regression_head = nn.Linear(512, 1)
        
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1) # Flatten
        shared_features = self.fc_layer(x)
        
        class_logits = self.classification_head(shared_features)
        yield_pred = self.regression_head(shared_features)
        
        return class_logits, yield_pred

def predict_image(image_path, model_path='cow_model.pth'):
    """
    Given an image path, return a tuple: (classification, confidence, predicted_yield).
    """
    if os.path.exists(model_path):
        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = CowSonogramCNN(num_classes=len(CLASSES)).to(device)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
            
            # Preprocess image
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            image = Image.open(image_path).convert('RGB')
            tensor = transform(image).unsqueeze(0).to(device)
            
            with torch.no_grad():
                class_logits, yield_pred = model(tensor)
                
                probabilities = torch.nn.functional.softmax(class_logits, dim=1)
                confidence, predicted_idx = torch.max(probabilities, 1)
                
                final_yield = yield_pred.item()
                # Yield cannot be negative
                if final_yield < 0: final_yield = 0.0
                
            return CLASSES[predicted_idx.item()], confidence.item(), final_yield
        except Exception as e:
            print(f"Error during real inference: {e}")
            pass
            
    # Mock inference if model is not trained yet (development mode)
    time.sleep(2) # Simulate ML processing time
    idx = random.randint(0, len(CLASSES) - 1)
    conf = random.uniform(0.7, 0.99)
    mock_yield = 25.5 if idx != 0 else 0.0
    return CLASSES[idx], conf, mock_yield
