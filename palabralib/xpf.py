from xml import sax
from xml.sax import make_parser

XPF_SUPPORT = 1.0
META_ELEMS = ['Type'
    , 'Title'
    , 'Author'
    , 'Editor'
    , 'Copyright'
    , 'Publisher'
    , 'Date']

class XPFContentHandler(sax.ContentHandler):
    def __init__(self):
        self.puzzles = []
        self.metadata = {'Type': 'normal'}
        self.curMetaElement = None
        self.inSizeElement = False
        
    def startElement(self, name, attrs):
        if name == 'Puzzles':
            v = attrs.get('Version', None)
            if v:
                self.xpf_version = float(v)
                if self.xpf_version > XPF_SUPPORT:
                    raise sax.SAXException('version not supported')
        if name in META_ELEMS:
            self.curMetaElement = name
            self.metadata[name] = ''
        if name in ['Rows', 'Cols']:
            self.inSizeElement = True
            self.size = ''
        if name == 'Grid':
            try:
                self.size = (self.width, self.height)
            except AttributeError:
                raise sax.SAXException('size not there')
            
    def characters(self, ch):
        if self.curMetaElement:
            self.metadata[self.curMetaElement] += ch
        if self.inSizeElement:
            self.size += ch
            
    def endElement(self, name):
        if self.curMetaElement:
            self.curMetaElement = None
        if self.inSizeElement:
            if name == 'Rows':
                self.width = int(self.size)
            elif name == 'Cols':
                self.height = int(self.size)
            self.inSizeElement = False
        
handler = XPFContentHandler()
parser = make_parser()
parser.setContentHandler(handler)
parser.parse('Mar08-2011.xml')
print handler.metadata, handler.width, handler.height
