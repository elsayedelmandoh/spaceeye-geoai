import os.path as path
import zipfile,re
from xml.dom import minidom
z=zipfile.ZipFile(path.join(__dirname, '..', 'presentation.pptx'))
sl=[n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$',n)]
nt=[n for n in z.namelist() if re.match(r'ppt/notesSlides/notesSlide\d+\.xml$',n)]
for n in z.namelist():
    if n.endswith('.xml') or n.endswith('.rels'): minidom.parseString(z.read(n))
print('slides',len(sl),'notes',len(nt),'all xml parsed')
md=open(path.join(__dirname, '..', 'presentation.md')).read()
print('md slides',len(re.findall(r'^## Slide',md,re.M)))
