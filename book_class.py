import os
import requests
from base64 import b64encode
from pathlib import Path
from mimetypes import guess_type
from google.cloud import vision

try:
    from lib.full_gcv2hocr.fulltext import FullText
    from lib.hocr2pdf import Hocr2Pdf
    from cloud_vision_counter import CVCounterOnline
except ImportError:
    from .lib.full_gcv2hocr.fulltext import FullText
    from .lib.hocr2pdf import Hocr2Pdf
    from .cloud_vision_counter import CVCounterOnline


IGNORES = [
    'zWater.jpg', 'zzzzRacerXtag20086a.jpg',
    'zzZone2.jpg', 'zzZone.jpg', 'zSoU-Nerd.jpg',
    'zzTLK.jpg', 'xBluntmanx.jpg',
    'Thumb.db', 'zzz_UberSoldierDCPDigital.jpg',
    'xsou5b.jpg', 'zz.jpg',
    'zzzMarika-Empire.jpg'
]


def is_image(fp):
    if fp.name in IGNORES:
        fp.unlink()
        return False
    typ, _enc = guess_type(str(fp))
    if typ and typ.startswith('image/'):
        return True
    return False


def detect(fp, client, language_hints):
    content = fp.read_bytes()
    image = vision.Image(content=content)
    response = client.document_text_detection(
        image=image,
        image_context={'language_hints': language_hints}
    )
    js = vision.AnnotateImageResponse.to_json(response)
    return js


class Book:
    def __init__(self, service_account_path=None, language_hints=['en'], gas_url=None):
        # サービスアカウント
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)
        self.client = vision.ImageAnnotatorClient()
        self.language_hints = language_hints
        self.counter = CVCounterOnline(service_account_path.stem, gas_url)

    def make_gcv_jsons(self, img_dr, json_dr):
        self.imgs = sorted(img_dr.glob('**/*'), key=lambda x: x.name)
        self.imgs = [ip for ip in self.imgs if is_image(ip)]
        len_ = len(self.imgs)
        if self.counter.cur_count() + len_ >= self.counter.max:
            raise ValueError('Limit')
        for i, ip in enumerate(self.imgs):
            jp = (json_dr / ip.name).with_suffix('.json')
            if jp.exists():
                print(f'{jp.name} exists')
                continue
            js = detect(ip, self.client, self.language_hints)
            jp.write_text(js)
            print(f'create {jp.name} {i + 1}/{len_}')

    def make_hocrs(self, json_dr, hocr_dr):
        for jp in sorted(json_dr.glob('*.json'), key=lambda x: x.name):
            hp = hocr_dr / jp.with_suffix('.hocr').name
            if hp.exists():
                print(f'{hp.name} exists')
                continue
            ft = FullText(jp, hp)
            if not ft.pages:
                print(f'{hp.name} no pages')
                continue
            ft.to_hocr()
            print(f'create {hp.name}')

    def to_pdf(self, img_dr, hocr_dr, pdf_p, single_page_h, invisible=True):
        h2p = Hocr2Pdf(img_dr, hocr_dr, pdf_p, single_page_h, invisible)
        if not pdf_p.exists() or pdf_p.stat().st_size == 0:
            h2p.export()
            self.counter.cur_count()

    def add_issue_count(self):
        issue_count = len(self.imgs)
        self.counter.add_issue_count(issue_count)


def main():
    """Main."""
    dr = Path('/Users/th/Downloads/2022-09-18/watchmen_test')
    # book = Book(dr)
    # book.make_gcv_jsons()
    # book.make_hocrs()  # hocrはgoogleドライブに保存しておきたい
    # book.make_one_hocr()

    h2p = Hocr2Pdf(dr=dr)
    h2p.dpi = None
    # h2p.invisible = False
    # h2p.width_ratio = 100.0 * 0.5
    h2p.set_hocr_root()
    h2p.export_from1()


if __name__ == '__main__':
    main()
