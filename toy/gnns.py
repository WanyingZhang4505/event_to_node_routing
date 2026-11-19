import torch
import torch.nn as nn
import torch.nn.functional as F

# def norm_adj(A, add_self=True):
#     if add_self: A = A + torch.eye(A.size)
#     deg = 

A = torch.randn(2,3,4)
print(A)