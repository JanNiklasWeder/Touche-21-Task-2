import xml.etree.ElementTree as ET
tree = ET.parse('topics-task-2.xml')
root = tree.getroot()
topics_file = open('topics_touche20.txt', 'w')
i = 1
for title in root.iter('title'):
    print(str(i) + ": " + title.text.strip())
    topics_file.write(title.text.strip()+"\n")
    i=i+1