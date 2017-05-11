from skimage import draw
import numpy as np

coords = []
f = open("room.txt")
line = f.readline().strip().split()
x = int(line[0])
y = int(line[1])
a = np.zeros((y, x), dtype=str)

for newline in range(y):
    text = f.readline().strip()
    a[newline] = list(text)
    print(text)

print(a)

