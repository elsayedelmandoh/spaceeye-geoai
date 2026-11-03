import zipfile,re
from xml.dom import minidom
z=zipfile.ZipFile('docs/deliverables/01-presentation.pptx')
sl=[n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$',n)]
nt=[n for n in z.namelist() if re.match(r'ppt/notesSlides/notesSlide\d+\.xml$',n)]
for n in z.namelist():
    if n.endswith('.xml') or n.endswith('.rels'): minidom.parseString(z.read(n))
print('slides',len(sl),'notes',len(nt),'all xml parsed')
md=open('docs/deliverables/01-presentation.md').read()
print('md slides',len(re.findall(r'^## Slide',md,re.M)))
