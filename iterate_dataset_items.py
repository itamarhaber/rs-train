import os
from util import InputItem

path = './dataset/'

# Get all files in the dataset folder that end with .md
files = [f for f in os.listdir(path) if f.endswith(".md")]
files.sort()

# Loop through all input files
for i in range(len(files)):
  item = InputItem(path + files[i])