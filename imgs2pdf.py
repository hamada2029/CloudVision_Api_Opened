from pathlib import Path
from pyunpack import Archive
import shutil
from PIL import Image


try:
    from book_class import Book
except ImportError:
    from .book_class import Book


def stem_filename(fp):
    nm = fp.name
    if '.' not in nm:
        return nm
    ws = nm.split('.')[:-1]
    return '.'.join(ws)


# comic book: 6.625 inches x 10.25 inches = 16.8275cm x 26.035cm

class Imgs2Pdf:
    def __init__(
            self,
            fp,  # directory or archive
            single_page_h=10.25,  # comic book height inch
            visible=False,
            remove=True,
            service_account_path=None,
            language_hints=['en'],
            gas_url=None
        ):
        self.fp = fp
        self.stem_name = stem_filename(fp)
        self.pdf_p = fp.parent / (self.stem_name + '.pdf')
        self.bkdr = fp.parent / self.stem_name
        self.bkdr.mkdir(exist_ok=True)
        self.img_dr = self.bkdr / 'img'
        self.img_dr.mkdir(exist_ok=True)
        self.hocr_dr = self.bkdr / 'hocr'
        self.hocr_dr.mkdir(exist_ok=True)
        self.json_dr = self.bkdr / 'json'
        self.json_dr.mkdir(exist_ok=True)
        self.single_page_h = single_page_h
        self.visible = visible
        self.remove = remove
        self.img_exts = ['*.jpg', '*.jpeg', '*.png', '*.webp']
        self.service_account_path = service_account_path
        self.language_hints = language_hints
        self.gas_url = gas_url

    def extract(self):
        if self.fp.is_dir():
            for img_ext in self.img_exts:
                for img_fp in self.fp.glob(img_ext):
                    shutil.copy(str(img_fp), str(self.img_dr))
        else:
            Archive(str(self.fp)).extractall(str(self.img_dr))

    def re_comp_imgs(self):
        for fp in self.img_dr.iterdir():
            ext = fp.name.split('.')[-1]
            if ext in ['jpg', 'jpeg']:
                im = Image.open(str(fp))
                im.save(str(fp), progressive=True, optimize=True)

    def render(self):
        book = Book(self.service_account_path, self.language_hints, self.gas_url)
        book.make_gcv_jsons(self.img_dr, self.json_dr)
        book.add_issue_count()
        book.make_hocrs(self.json_dr, self.hocr_dr)
        book.to_pdf(
            self.img_dr,
            self.hocr_dr,
            self.pdf_p,
            self.single_page_h,
            not self.visible
        )

        if self.remove:
            if self.fp.is_dir():
                shutil.rmtree(str(self.img_dr))
                shutil.rmtree(str(self.json_dr))
                shutil.rmtree(str(self.hocr_dr))
            else:
                shutil.rmtree(str(self.bkdr))

        print('done', self.stem_name)


def main():
    """Main."""
    fp = '/tmp/tmp.cbr'
    i2p = Imgs2Pdf(
        fp,
        dpi=None,
        visible=False,
        remove=True
    )
    i2p.extract()
    i2p.render()


if __name__ == '__main__':
    main()
