import os
from util import InputItem
import frontmatter

path = './redisearch-docs/'

# Get all files in the dataset folder that end with .md
files = [f for f in os.listdir(path) if f.endswith(".md") and f.startswith("ft.")]
files.sort()

# Loop through all input files
output = open('./redisearch-docs/commands.md', 'w')
for i in range(len(files)):
  with open(path + files[i]) as f:
    post = frontmatter.load(f)
    output.write('# ' + post['title'] + '\n')
    output.write('## Syntax\n')
    output.write('```\n')
    output.write(post['syntax_str'])
    output.write('```\n\n')
    output.write(post.content)
    output.write('\n')
output.close()