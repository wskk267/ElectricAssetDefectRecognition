import pymysql
import os
import hashlib
def sha256_hash(text):
    """计算SHA-256哈希值"""
    return hashlib.sha256(text.encode()).hexdigest()
print(sha256_hash("admin123"))
t=1
cnt=0
if os.path.exists("best.pt"):
    print(f"{t}. 设备识别模型best.pt存在 ")
else:
    print(f"{t}. 设备识别模型best.pt不存在 ")
    cnt+=1

t+=1
if os.path.exists("last.pt"):
    print(f"{t}. 缺陷分类模型last.pt存在 ")
else:
    print(f"{t}. 缺陷分类模型last.pt不存在 ")
    cnt+=1


