# datasets
```
1. dataset --> 2. transform --> 3. loader
```

# all datasets go over transformation in some sort 
```markdown
from images.datasets.singlefolder_dataset import SingleFolderDataset
from images.datasets.dataframe_dataset import DataFrameDataset

# -- transformation
transform = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.GaussianBlur(kernel_size=(5, 9), sigma=(0.1, 5)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# -- init
dataset = SingleFolderDataset('path/to/your/single/folder', transform)

# -- loader
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
```
