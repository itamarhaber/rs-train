import frontmatter

# An abstraction of an input item section
class InputItemSection(object):
  def __init__(self, name: str, content: [str]):
    self.name = name
    self.content = content

# An abstraction of an input item
class InputItem(object):
  def __init__(self, path):
    self.path = path
    self.headings = {}
    self.sections = []
    self.post = frontmatter.load(path)
    lines = self.post.content.split('\n')

    curr = None
    for line in lines:
      # Convert h2 to section
      if line.startswith('##'):
        heading = line[3:].strip()
        curr = InputItemSection(heading, [])
        self.append(curr)
      else:
        curr.content.append(line)

  def append(self, section: InputItemSection) -> None:
    self.sections.append(section)
    self.headings[section.name] = section
  
  def set(self, heading: str, lines: [str]) -> None:
    if heading not in self.headings:
        self.append(InputItemSection(heading, lines))
    else:
        self.headings[heading].content = lines

  def get(self, heading: str) -> [str]:
    if heading not in self.headings:
      return []
    return self.headings[heading].content

  def get_code(self, heading: str) -> [str]:
    if heading not in self.headings:
      return []
    return '\n'.join([l for l in self.headings[heading].content if not l.startswith('```')]).strip()

  def delete(self, heading: str) -> None:
    if heading not in self.headings:
      return
    del self.headings[heading]
    for i, s in enumerate(self.sections):
      if s.name == heading:
        del self.sections[i]
        return

  def dumps(self) -> str:
    s = ''
    for section in self.sections:
      s += f'## {section.name}\n'
      for line in section.content:
        s += f'{line}\n'
      if line !='':
        s += '\n'
    self.post.content = s
    return frontmatter.dumps(self.post)
  
  def dump(self, path=None) -> None:
    if path is None:
      path = self.path
    with open(path, 'w') as f:
      f.write(self.dumps())

def main():
  input = './dataset/a0000.md'
  item = InputItem(input)
  item.dump('./dataset/a0000-test.md')

if __name__ == '__main__':
  main()