"""Read bounded PDF/HWPX attachments without executing document contents."""
from io import BytesIO
import zipfile
from xml.etree import ElementTree
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text

MAX_BYTES = 12 * 1024 * 1024


def attachment_links(markup, base):
    soup = BeautifulSoup(markup, 'html.parser')
    result = []
    for a in soup.select('a[href]'):
        href = a.get('href', '')
        if href.startswith(('javascript:', '#')):
            continue
        if any(v in (href + ' ' + a.get_text()).lower() for v in ('.pdf', '.hwpx', '.zip', 'download', 'filedown', '첨부')):
            url = urljoin(base, href)
            if url.startswith(('https://', 'http://')) and url not in result:
                result.append(url)
    return result[:3]


def document_text(data):
    if len(data) > MAX_BYTES:
        raise ValueError('Attachment exceeds 12 MiB')
    if data.startswith(b'%PDF'):
        return extract_text(BytesIO(data), maxpages=25)[:90000]
    if data.startswith(b'PK'):
        with zipfile.ZipFile(BytesIO(data)) as z:
            entries = z.infolist()
            if sum(i.file_size for i in entries) > 30 * 1024 * 1024:
                raise ValueError('Expanded document too large')
            sections = [i for i in entries if i.filename.startswith('Contents/section') and i.filename.endswith('.xml')]
            if sections:
                return '\n'.join(' '.join(ElementTree.fromstring(z.read(i)).itertext()) for i in sections)[:90000]
            return '\n'.join(extract_text(BytesIO(z.read(i)), maxpages=20) for i in entries if i.filename.lower().endswith('.pdf'))[:90000]
    return ''
