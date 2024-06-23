#-*- coding:utf-8 -*-  
import numpy as np
import os, glob
import cv2
import math
import imageio
from math import log10
import random
import torch
import torch.nn as nn
import torch.nn.init as init
from PIL import Image
# from skimage.measure.simple_metrics import compare_psnr
from skimage.metrics.simple_metrics import peak_signal_noise_ratio
from skimage.metrics import peak_signal_noise_ratio
imageio.plugins.freeimage.download()

def check_directory(directory):
    if not directory:
        raise FileExistsError("File or directory not found")
    if directory[-1] != "/":
        directory += "/"
    return directory


def get_all_files(parent_directory, suffix=""):
    return list(
        filter(
            lambda x: os.path.isfile(os.path.join(parent_directory, x))
            and x.endswith(suffix),
            os.listdir(parent_directory),
        )
    )

def list_all_files_sorted(folder_name, extension=""):
    return sorted(glob.glob(os.path.join(folder_name, "*" + extension)))

def read_expo_times(file_name):
    return np.power(2, np.loadtxt(file_name))

def read_images(file_names):
    imgs = []
    for img_str in file_names:
        img = cv2.cvtColor(cv2.imread(img_str), cv2.COLOR_BGR2RGB) / 255.0
        imgs.append(img)
    return np.array(imgs)

def imread_uint16_png(image_path):
    # Load image without changing bit depth
    return cv2.cvtColor(cv2.imread(image_path, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB)

def read_label(file_path, file_name):
    label = imread_uint16_png(os.path.join(file_path, file_name))
    return label

def gamma_correction( img, expo, gamma):
    return (img ** gamma) / 2.0 ** expo

def ldr_to_hdr(imgs, expo, gamma):
    return (imgs ** gamma) / (expo + 1e-8)

def range_compressor(x):
    return (np.log(1 + 5000 * x)) / np.log(1 + 5000)

def range_compressor_cuda(hdr_img, mu=5000):
    return (torch.log(1 + mu * hdr_img)) / math.log(1 + mu)

def range_compressor_tensor(x, device):
    a = torch.tensor(1.0, device=device, requires_grad=False)
    mu = torch.tensor(5000.0, device=device, requires_grad=False)
    return (torch.log(a + mu * x)) / torch.log(a + mu)

def psnr(x, target):
    sqrdErr = np.mean((x - target) ** 2)
    return 10 * log10(1/sqrdErr)

def batch_psnr(img, imclean, data_range):
    Img = img.data.cpu().numpy().astype(np.float32)
    Iclean = imclean.data.cpu().numpy().astype(np.float32)
    psnr = 0
    for i in range(Img.shape[0]):
        psnr += peak_signal_noise_ratio(Iclean[i,:,:,:], Img[i,:,:,:], data_range=data_range)
    return (psnr/Img.shape[0])

def batch_psnr_mu(img, imclean, data_range):
    img = range_compressor_cuda(img)
    imclean = range_compressor_cuda(imclean)
    Img = img.data.cpu().numpy().astype(np.float32)
    Iclean = imclean.data.cpu().numpy().astype(np.float32)
    psnr = 0
    for i in range(Img.shape[0]):
        psnr += peak_signal_noise_ratio(Iclean[i,:,:,:], Img[i,:,:,:], data_range=data_range)
    return (psnr/Img.shape[0])

def adjust_learning_rate(args, optimizer, epoch):
    lr = args.lr * (0.5 ** (epoch // args.lr_decay_interval))
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr

def init_parameters(net):
    """Init layer parameters"""
    for m in net.modules():
        if isinstance(m, nn.Conv2d):
            init.kaiming_normal_(m.weight, mode='fan_out')
            if m.bias is not None:
                init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm2d):
            init.constant_(m.weight, 1)
            init.constant_(m.bias, 0)
        elif isinstance(m, nn.Linear):
            init.xavier_normal_(m.weight)
            init.constant_(m.bias, 0)

def set_random_seed(seed):
    """Set random seed for reproduce"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def radiance_writer(out_path, image):

    with open(out_path, "wb") as f:
        f.write(b"#?RADIANCE\n# Made with Python & Numpy\nFORMAT=32-bit_rle_rgbe\n\n")
        f.write(b"-Y %d +X %d\n" %(image.shape[0], image.shape[1]))

        brightest = np.maximum(np.maximum(image[...,0], image[...,1]), image[...,2])
        mantissa = np.zeros_like(brightest)
        exponent = np.zeros_like(brightest)
        np.frexp(brightest, mantissa, exponent)
        scaled_mantissa = mantissa * 255.0 / brightest
        rgbe = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)
        rgbe[...,0:3] = np.around(image[...,0:3] * scaled_mantissa[...,None])
        rgbe[...,3] = np.around(exponent + 128)

        rgbe.flatten().tofile(f)

def save_hdr(path, image):
    return radiance_writer(path, image)

def read_images(
    directory,
    read_mode="cv",
    isColorConvert=True,
    suffix=""
):
    directory = check_directory(directory)
    fileName_list = get_all_files(directory, suffix=suffix)
    imgs = []
    for fileName in fileName_list:
        filePath = os.path.join(directory, fileName)
        if read_mode.lower() == "cv":
            img = cv2.imread(filePath)
            if img is None:
                raise FileNotFoundError
            if isColorConvert:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif read_mode.lower() == "pil":
            tmp = Image.open(filePath)
            img = tmp.copy()
            tmp.close()
        imgs.append(img)
    return imgs



