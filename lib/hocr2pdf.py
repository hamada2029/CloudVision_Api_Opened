import re
from lxml import etree, html
from mimetypes import guess_type
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch


# REP_P1 = re.compile('(--+)$')  # 2つ以上の文末の -
REP_P1 = re.compile('([^- ])(-+)')

def replace_word(word):
    # print(word)
    # word = REP_P1.sub(r'\1 \2', word)
    # print(word)
    return word


class OcrImg:
    """docstring for OcrImg"""
    def __init__(self, fp):
        self.fp = fp
        self.stem = fp.stem
        self.typ = guess_type(str(fp))[0]
        self.image = None
        if self.is_image():
            self.image = ImageReader(str(fp))

    def is_image(self):
        if self.typ and self.typ.startswith('image/'):
            return True
        return False

    def is_single(self):
        if not self.image:
            return False
        return True

    def bio(self):
        return BytesIO(self.fp.read_bytes())


def polyval(poly, x):
    return x * poly[0] + poly[1]


class Hocr2Pdf:
    """docstring for Hocr2Pdf"""
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    p1 = re.compile(r'bbox((\s+\d+){4})')
    p2 = re.compile(r'baseline((\s+[\d\.\-]+){2})')
    RED = (1, 0, 0)
    WHITE = (1, 1, 1)
    GRAY = (0.5, 0.5, 0.5)

    def __init__(self, img_dr, hocr_dr, pdf_p, single_page_h, invisible):
        self.pdf = Canvas(
            str(pdf_p),
            pageCompression=1
        )
        self.pdf.setCreator('reportlab and hocr-tools')
        self.pdf.setTitle(pdf_p.name)
        self.images = [OcrImg(fp=fp) for fp in img_dr.glob('**/*')]
        self.images = [oi for oi in self.images if oi.is_image()]
        self.images = sorted(self.images, key=lambda x: x.fp.name)
        self.hocr_dr = hocr_dr
        self.single_page_h = single_page_h
        self.invisible = invisible
        # self.font_size_ratio = 1 * 0.8
        self.font_size_ratio = 1.0
        # 幅いっぱいにするとlookupで隣とくっつく
        # self.width_ratio = 48.0
        # 狭すぎるとlookupで連続した同じ文字がくっつく
        self.width_ratio = 100.0  # * 0.8
        self.skip1char = False

    def export(self):
        for oi in self.images:
            w, h = oi.image.getSize()
            dpi = h / self.single_page_h
            print(f'dpi: {dpi}, height: {h / dpi}inch')
            w_point = w / dpi * inch
            h_point = h / dpi * inch
            self.pdf.setPageSize((w_point, h_point))
            self.pdf.drawImage(
                oi.image, 0, 0, width=w_point, height=h_point
            )
            self.add_text_layer(oi.stem, h_point, dpi)
            self.pdf.showPage()
            print(oi.stem)
        self.pdf.save()

    def _add_text_layer(self, hocr_page, h_point, dpi):
        """Draw an invisible text layer for OCR data"""
        pt_ratio = 72 / dpi

        for line in hocr_page.xpath('.//*[@class="ocr_line"]'):
            linebox = self.p1.search(line.attrib['title']).group(1).split()
            try:
                baseline = self.p2.search(line.attrib['title']).group(1).split()
            except AttributeError:
                baseline = [0, 0]
            linebox = [float(i) for i in linebox]
            baseline = [float(i) for i in baseline]
            for word in line.xpath('.//*[@class="ocrx_word"]'):
                rawtext = word.text_content().strip()
                if rawtext == '':
                    continue
                if self.skip1char and len(rawtext) == 1:
                    continue

                # rawtext += ' '  # 間開けてみる
                rawtext = replace_word(rawtext)

                # left top right bottom (x0, y0, x1, y1)
                box = self.p1.search(word.attrib['title']).group(1).split()
                box = [float(i) for i in box]
                # print(box)
                # wrd_w = box[2] - box[0]
                wrd_h = (box[3] - box[1]) * pt_ratio

                if wrd_h >= 100:
                    continue

                # print('wrd_w:', wrd_w)
                # print('wrd_h:', wrd_h)
                font_size = wrd_h * self.font_size_ratio
                font_size = 8 if font_size < 8 else font_size
                font_width = self.pdf.stringWidth(
                    rawtext, 'HeiseiKakuGo-W5', font_size
                )
                if font_width <= 0:
                    continue
                # base_df = wrd_h / 5  # ちょっと上げる？
                baseline = [baseline[0], baseline[1]]
                b = polyval(
                    baseline,
                    (box[0] + box[2]) / 2 - linebox[0]
                ) + linebox[3]
                text = self.pdf.beginText()
                if self.invisible:
                    text.setTextRenderMode(3)    # double invisible
                text.setFillColorRGB(*self.RED)
                text.setFont('HeiseiKakuGo-W5', font_size)
                # x_df = (wrd_w - font_width) / 2
                y_df = (wrd_h - font_size) / 2
                text.setTextOrigin(
                    box[0] * pt_ratio,  # + x_df,
                    h_point - b * pt_ratio + y_df
                )
                box_width = (box[2] - box[0]) * pt_ratio
                text.setHorizScale(
                    box_width / font_width * self.width_ratio
                )
                text.textLine(rawtext)
                self.pdf.drawText(text)

    def add_text_layer(self, stem, h_point, dpi):
        """Draw an invisible text layer for OCR data"""
        hocr_p = self.hocr_dr / (stem + '.hocr')
        if not hocr_p.exists():
            return
        hocr_page = etree.parse(str(hocr_p), html.XHTMLParser())
        self._add_text_layer(hocr_page, h_point, dpi)


def main():
    """Main."""


if __name__ == '__main__':
    main()
