# 基于扩散模型实现高质量HDR图像恢复 —— 2024 Spring Computer Vision Final Project  

# 这里仅展示项目报告中的方法、实验**部分**以及**部分**结果展示，完整项目报告请于仓库中查阅 
  
## [B站视频链接（可能还在审核，请耐心等待哦~）](https://space.bilibili.com/1076908343?spm_id_from=333.1007.0.0)
  
## 综述 
  
   本文研究了基于扩散模型的高质量HDR图像恢复技术。随着深度学习的发展，尤其是生成式模型如 GAN 和 扩散模型 的兴起，HDR图像合成的研究逐渐从依赖多张不同曝光的图像合成向单张图像和无监督学习方向发展。本文提出了一个基于条件扩散模型的HDR扩散模型，通过特征条件生成器（FCG）和滑动窗口噪声估计方法（SWNE）等技术，有效提升了HDR图像的质量，并减少了扩散模型的迭代次数。实验结果显示，本方法能够生成高质量的HDR图像，并且在视觉上与真实场景高度一致。 
   
  
## 方法 
  
  本文中 HDR 扩散模型（HDR Diffusion Model）是基于扩散模型进行开发的。 
### 模型基础——扩散模型 
  扩散过程是一个 T 步马尔可夫链，在输入图像 x0 上逐步加噪使其最终变成各向同性的高斯噪声图像。逆向去噪：反向过程基于马尔可夫链 ，对正向过程添加的高斯噪声进行估计，最终去噪生成图像。 
### HDR 扩散模型 
  我们的模型是基于扩散模型从一组具有不同曝光的 LDR 图像中恢复出 HDR图像，我们没有改变条件扩散模型SDE原本的扩散方程，而是通过设计一个特征条件生成器FCG将LDR图像的特征转换为去噪过程的条件，通过在每个逆时间步骤添加LDR特征信息来指导特定HDR图像的恢复。 
  接下来将介绍 FCG 具体如何实现。 
####  FCG.
首先通过注意力模块 AM 进行隐式特征对齐，这种注意力机制能够解决多张 LDR 图像存在曝光差异和运动情况下产生的难以对齐而导致的重影问题，且在这种情况下仍然可以提取图像中的关键特征；接着 FCG 使用域特征对齐（DFA）的层来进一步处理这些特征，DFA 层的函数是由多个卷积层构造的，这个函数能够将提取出的特征映射到一个适合于去噪过程的参数空间，将特征转换为参数空间中的调节参数；紧接着，这些调节参数被用来仿射变换去噪器网络中的中间特征图，仿射变换后的参数能够被去噪网络在去噪过程中使用，去噪网络可以根据这些参数来预测可能会产生的噪声并进行消去，通过消去由原本多张 LDR图像特征生成的参数预测的噪声，图像就会展现出 LDR 图像共同的重建图像，即HDR 图像。在此过程中，FCG 成功帮助了在逆向去噪过程中添加 LDR 参数来合成高质量 HDR 图像的过程，并且由于 FCG 处理过程中不受 LDR 图像存在大范围运动和曝光不一致的情况的影响，该方法合成的 HDR 图像也不会受其影响。 
###  滑动窗口噪声估计方法 SWNE 
  在 HDR 图像生成中，直接预测整个图像的噪声可能导致细节信息的丢失或者引发重影的出现，SWNE 通过在局部区域内平滑地估计噪声，有助于缓解这些问题。过程：首先 SWNE 将图像分解为大小为 r × r 像素的网格状排列的单元格，随后使用一个大小为 p×p 像素的滑动窗口在这个网格上移动。窗口的移动步长为r，这样就可以以滑动窗口的方式遍历整个图片。对于每个噪声窗口通过使用一个二进制掩码矩阵与滑动窗口内的图像矩阵进行点乘来得到该噪声窗口的噪声估计，完成所有迭代后计算平滑噪声估计并用于逆向去噪之中，这种方法的好处在于通过计算所有窗口的平滑噪声估计，可以降低由于曝光不一致或者大范围云顶引起的不自然噪声，从而在逆向去噪的过程中生成一个更自然更高质量的图像。 
### 解决颜色失真问题 
  在对 HDR 的扩散模型的逆向去噪过程中，如果处理的是 LDR 图像的饱和区域，会由于直接在噪声空间中操作而没有对生成的图像像素进行约束而产生颜色失真现象。因此，我们使用了一个损失函数——图像空间损失，该损失函数不再在噪声空间中直接对 LDR 图像进行操作，而是通过逆过程将噪声转换回图像空间，进而直接处理和优化图像像素。 
### 减少扩散模型的迭代次数 
  由于传统扩散模型需要大量迭代次数来完成训练，为了减少训练时间，基于 DDIM，通过使用隐式采样的方式使用非马尔科夫链前向过程来解决了马尔可夫链的不断缓慢迭代过程，加速了图像生成的速度，同时保障了图像的质量。 
  
## 实验 
### 实验设置 
#### 数据集设置 
  我们实验使用 Kalantari 的数据集 [4] 进行实验，其中包括 70 个用于训练的样本和 15 个用于预测的样本。对每个样本，在一个动态场景上捕获三张曝光时间不同的 LDR 图像，训练集中包括真实的 HDR 图像作为 ground true，测试集仅通过三张 LDR 图像进行推断。我们将每个样本分成了多个 patch，并对其进行数据增强，包括随机水平或垂直翻转以及顺时针或逆时针旋转等。 

#### 评估指标 
  SSIM （Structural Similarity Index）是一种全参考图像质量评估方法，即它需要一个无损的原始图像作为参考，然后对失真图像进行评估。它的基本思想是，将图像分成亮度、对比度和结构三个部分，然后分别计算这三个部分的相似度，并将它们组合成一个总的相似度指数。SSIM 的值范围在 -1 到 1 之间，值越大表示图像质量越好，常用于图像压缩、去噪、增强和其他图像处理任务中的客观质量评估。 
  LPIPS （Learned Perceptual Image Patch Similarity）是一种用于衡量图像相似性的指标。与传统的图像质量评估方法（如 PSNR 和 SSIM ）相比，LPIPS 更接近人类视觉系统的感知。它通过训练一个深度神经网络来学习图像块之间的相似性和差异性，从而能够捕捉到人类视觉系统所关注的细节，更准确地反映人眼对图像质量的感知。此外，LPIPS 能够适应不同的图像内容和风格，对于评估本项目中经过复杂图像处理技术得到的图像特别有用。首先利用预训练的卷积神经网络生成的 HDR 图像 x 真实的 HDR 图像 y 的特征，然后计算这些特征在不同层之间的距离，最后将所有层的距离进行加权求得最终的相似性分数。 
  结合使用 SSIM 和 LPIPS 可以提供更全面的图像质量评估，SSIM 提供了快速且直观的评估，而 LPIPS 提供了更深入和细致的感知评估，能够全面地评估基于条件扩散模型实现高质量 HDR 图像修复技术的性能，确保恢复生成的 HDR 图像不仅在视觉上与原始场景保持高度一致，而且在感知质量上也能满足高标准。 

#### 实现细节 
  我们对模型进行了 30 次迭代的训练。在扩散模型的每次训练迭代中，我们从训练集中对每个图像中进行滑动窗口裁剪，得到 77 个大小为 128×128 的 patch，并对其进行数据增强，并设置每个 batch 包含 32 张增强后的图像。我们使用 β1 = 0.9，β2 = 0.999 的 Adam 优化器和 2 × 10−5 的固定学习率。在参数更新期间应用了权重为 0.999 的指数移动平均。所有实验都基于 PyTorch 实现，并在 4090 服务器的GPU 上进行训练和预测。 

### 实验结果 
#### 定性结果 
  ![image](https://github.com/OUC-CV/final-project-ouc-sota/assets/106426328/17688147-cc66-4aaa-ab9b-06d3340452ef) 

  ![image](https://github.com/OUC-CV/final-project-ouc-sota/assets/106426328/080cde84-8a84-4566-bc84-33a59e1df734) 
  
定性结果如图 4-1, 图 4-2 和图 4-3 所示，上方是 Ground True，下方是我们的方法实现的结果，两者非常接近。从图中可以看到，我们的结果不仅非常清晰， 而且对能够较好地对其不同的曝光图像，达到了高动态范围稳定成像的效果。更多的结果可以从我们的仓库中查看。 

#### 定量结果 
  ![image](https://github.com/OUC-CV/final-project-ouc-sota/assets/106426328/d5db5bd8-cb6e-4ec0-a645-b7d91bbdc980) 
  
SSIM 越接近 1，LPIPS 越接近 0，表明模型效果越好。我们方法的定量结果如表 4-1 所示，可以看到，我们方法的 SSIM 非常接近 1，且 LPIPS 非常接近 0，表明我们的方法以及达到了高质量的图像恢复效果。将我们方法的 SSIM 和 LPIPS 指标与原文相比，也都达到了非常接近的程度，表明我们的方法的定量结果也非常令人满意。
