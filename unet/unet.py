import torch
import torch.nn as nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels, mid_channels = None):
        super(DoubleConv, self).__init__()
        if not mid_channels:
            mid_channels = out_channels

        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        return self.conv(x)
    
class DownConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DownConv, self).__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels)
        )
    
    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    def __init__(self, in_channels, out_channels, bilinear=True) -> None:
        super(Up, self).__init__()

        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, in_channels//2)
        else:
            self.up = nn.ConvTranspose2d(
                in_channels,
                in_channels//2,
                kernel_size=2,
                stride=2
            )
            self.conv = DoubleConv(in_channels, out_channels)

    # def crop_img(self, tensor, target_tensor):
    #     target_size = target_tensor.size()[2]
    #     tensor_size = tensor.size()[2]
    #     delta = tensor_size - target_size
    #     delta = delta // 2
    #     return tensor[:, :, delta:tensor_size-delta, delta:tensor_size-delta]
        
    def forward(self, x1, x2):
        x1 = self.up(x1)

        delta_y = x2.size()[2] - x1.size()[2]
        delta_x = x2.size()[3] - x1.size()[3]

        x1 = F.pad(x1, [delta_x//2, delta_x - delta_x//2,
                        delta_y//2, delta_y - delta_y//2])

        # x1 = self.crop_img(x1,x2)
        
        x = torch.cat([x2,x1], dim=1)
        return self.conv(x)
    
class OutConv(nn.Module):
    def __init__(self, in_channels, out_channels) -> None:
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)
    
    def forward(self, x):
        return self.conv(x)