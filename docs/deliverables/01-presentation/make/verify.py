import os.path as path

HERE = path.dirname(path.abspath(__file__))
import zipfile,re
from xml.dom import minidom
z=zipfile.ZipFile(path.join(HERE, '..', 'presentation.pptx'))
sl=[n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$',n)]
nt=[n for n in z.namelist() if re.match(r'ppt/notesSlides/notesSlide\d+\.xml$',n)]
for n in z.namelist():
    if n.endswith('.xml') or n.endswith('.rels'): minidom.parseString(z.read(n))
print('slides',len(sl),'notes',len(nt),'all xml parsed')
md=open(path.join(HERE, '..', 'presentation.md'), encoding='utf-8').read()
n_md=len(re.findall(r'^## Slide',md,re.M))
print('md slides',n_md)
html=open(path.join(HERE, '..', 'presentation.html'), encoding='utf-8').read()
n_html=len(re.findall(r'<section[\s>]',html))
print('html sections',n_html)
assert n_html==n_md, f'html sections {n_html} != md slides {n_md}'
assert (len(sl), len(nt), n_md, n_html) == (18, 18, 18, 18), (len(sl), len(nt), n_md, n_html)
