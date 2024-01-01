import torch
import torch.nn as nn

class PatchEmbed(nn.Module):
    """
    Image to Patch Embedding

    Process
    1. takes square images, patch sizes, embedding dim
    2. project channel to embedding dim
    3. flatten and transpose

    Return
    flattened patch tokens [B, N, C]
    """
    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768):
        super().__init__()
        num_patches = (img_size // patch_size) * (img_size // patch_size)
        self.img_size = img_size
        self.patch_size = patch_size
        self.num_patches = num_patches

        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        B, C, H, W = x.shape
        x = self.proj(x).flatten(2).transpose(1, 2)
        return x
