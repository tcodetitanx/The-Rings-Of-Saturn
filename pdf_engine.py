"""
Professional PDF Book Engine
Generates print-ready 6x9 trade paperback PDFs with proper typography.
"""

from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import black, white, HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Frame, PageTemplate,
    BaseDocTemplate, NextPageTemplate, FrameBreak, Table, TableStyle
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os

# Page dimensions: 6x9 inch trade paperback
PAGE_WIDTH = 6 * inch
PAGE_HEIGHT = 9 * inch

# Margins (asymmetric for binding)
MARGIN_INSIDE = 0.875 * inch
MARGIN_OUTSIDE = 0.625 * inch
MARGIN_TOP = 0.75 * inch
MARGIN_BOTTOM = 0.7 * inch

DARK_BG = HexColor('#0a0a0a')
ACCENT_CYAN = HexColor('#00d4ff')
ACCENT_CRIMSON = HexColor('#8b0000')
GREY_TEXT = HexColor('#333333')
LIGHT_GREY = HexColor('#999999')


class SectionBreak(Flowable):
    """A decorative section break (three centered dots or symbols)."""
    def __init__(self, symbol="* * *", width=PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE):
        Flowable.__init__(self)
        self.symbol = symbol
        self.width = width
        self.height = 24

    def draw(self):
        self.canv.setFont("Times-Roman", 11)
        self.canv.setFillColor(LIGHT_GREY)
        text_width = self.canv.stringWidth(self.symbol, "Times-Roman", 11)
        x = (self.width - text_width) / 2
        self.canv.drawString(x, 8, self.symbol)


class ChapterHeading(Flowable):
    """A styled chapter heading with number and title."""
    def __init__(self, number, title, style="cyberpunk"):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.style = style
        self.width = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE
        self.height = 180

    def draw(self):
        c = self.canv
        # Chapter number
        c.setFont("Times-Roman", 10)
        c.setFillColor(LIGHT_GREY)
        label = f"CHAPTER {self.number}"
        lw = c.stringWidth(label, "Times-Roman", 10)
        c.drawString((self.width - lw) / 2, 130, label)

        # Decorative line
        line_y = 120
        line_half = 60
        cx = self.width / 2
        c.setStrokeColor(LIGHT_GREY)
        c.setLineWidth(0.5)
        c.line(cx - line_half, line_y, cx + line_half, line_y)

        # Chapter title
        c.setFont("Times-Bold", 18)
        c.setFillColor(black)
        tw = c.stringWidth(self.title, "Times-Bold", 18)
        # Handle long titles
        if tw > self.width - 20:
            c.setFont("Times-Bold", 15)
            tw = c.stringWidth(self.title, "Times-Bold", 15)
        c.drawString((self.width - tw) / 2, 85, self.title)

        # Bottom decorative line
        c.setStrokeColor(LIGHT_GREY)
        c.line(cx - line_half, 75, cx + line_half, 75)


class BookBuilder:
    """Builds a professional print-ready PDF book."""

    def __init__(self, title, author, subtitle="", style="cyberpunk"):
        self.title = title
        self.author = author
        self.subtitle = subtitle
        self.style = style
        self.chapters = []
        self.dedication = ""
        self.epigraph = ""
        self.epigraph_attribution = ""
        self.copyright_text = ""
        self.part_titles = {}  # chapter_index -> part_title

    def set_dedication(self, text):
        self.dedication = text

    def set_epigraph(self, text, attribution=""):
        self.epigraph = text
        self.epigraph_attribution = attribution

    def set_copyright(self, text):
        self.copyright_text = text

    def add_part(self, before_chapter_index, part_title):
        self.part_titles[before_chapter_index] = part_title

    def add_chapter(self, title, text):
        """Add a chapter. Text uses \\n\\n for paragraph breaks and '***' for section breaks."""
        self.chapters.append({"title": title, "text": text})

    def _get_styles(self):
        """Create all paragraph styles for the book."""
        styles = {}

        styles['body'] = ParagraphStyle(
            'BookBody',
            fontName='Times-Roman',
            fontSize=11,
            leading=15,
            alignment=TA_JUSTIFY,
            firstLineIndent=18,
            spaceBefore=0,
            spaceAfter=2,
            textColor=black,
        )

        styles['body_first'] = ParagraphStyle(
            'BookBodyFirst',
            parent=styles['body'],
            firstLineIndent=0,
        )

        styles['title'] = ParagraphStyle(
            'BookTitle',
            fontName='Times-Bold',
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=8,
            textColor=black,
        )

        styles['subtitle'] = ParagraphStyle(
            'BookSubtitle',
            fontName='Times-Italic',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=GREY_TEXT,
        )

        styles['author'] = ParagraphStyle(
            'BookAuthor',
            fontName='Times-Roman',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceBefore=12,
            textColor=black,
        )

        styles['copyright'] = ParagraphStyle(
            'Copyright',
            fontName='Times-Roman',
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=GREY_TEXT,
        )

        styles['dedication'] = ParagraphStyle(
            'Dedication',
            fontName='Times-Italic',
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=GREY_TEXT,
        )

        styles['epigraph'] = ParagraphStyle(
            'Epigraph',
            fontName='Times-Italic',
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=GREY_TEXT,
            rightIndent=40,
            leftIndent=40,
        )

        styles['epigraph_attr'] = ParagraphStyle(
            'EpigraphAttr',
            fontName='Times-Roman',
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT,
            textColor=LIGHT_GREY,
            rightIndent=40,
        )

        styles['toc_title'] = ParagraphStyle(
            'TOCTitle',
            fontName='Times-Bold',
            fontSize=18,
            leading=24,
            alignment=TA_CENTER,
            spaceBefore=40,
            spaceAfter=30,
            textColor=black,
        )

        styles['toc_entry'] = ParagraphStyle(
            'TOCEntry',
            fontName='Times-Roman',
            fontSize=11,
            leading=20,
            alignment=TA_LEFT,
            leftIndent=20,
            textColor=black,
        )

        styles['part_title'] = ParagraphStyle(
            'PartTitle',
            fontName='Times-Bold',
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=black,
        )

        styles['part_label'] = ParagraphStyle(
            'PartLabel',
            fontName='Times-Roman',
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=LIGHT_GREY,
        )

        return styles

    def build(self, output_path):
        """Generate the PDF."""
        styles = self._get_styles()
        story = []

        # === HALF TITLE PAGE ===
        story.append(Spacer(1, 150))
        story.append(Paragraph(self.title, styles['title']))
        story.append(PageBreak())

        # === BLANK PAGE (verso of half title) ===
        story.append(Spacer(1, 1))
        story.append(PageBreak())

        # === FULL TITLE PAGE ===
        story.append(Spacer(1, 120))
        story.append(Paragraph(self.title, styles['title']))
        if self.subtitle:
            story.append(Spacer(1, 8))
            story.append(Paragraph(self.subtitle, styles['subtitle']))
        story.append(Spacer(1, 30))
        # Decorative rule
        story.append(Paragraph("_______________", ParagraphStyle(
            'rule', fontName='Times-Roman', fontSize=11, alignment=TA_CENTER,
            textColor=LIGHT_GREY
        )))
        story.append(Spacer(1, 30))
        story.append(Paragraph(self.author, styles['author']))
        story.append(PageBreak())

        # === COPYRIGHT PAGE ===
        story.append(Spacer(1, 350))
        if self.copyright_text:
            for line in self.copyright_text.split('\n'):
                story.append(Paragraph(line.strip(), styles['copyright']))
                story.append(Spacer(1, 2))
        else:
            story.append(Paragraph(f"{self.title}", styles['copyright']))
            story.append(Paragraph(f"Copyright \u00a9 2026 {self.author}", styles['copyright']))
            story.append(Spacer(1, 4))
            story.append(Paragraph("All rights reserved.", styles['copyright']))
            story.append(Paragraph("This is a work of fiction. Names, characters, places, and incidents", styles['copyright']))
            story.append(Paragraph("are products of the author's imagination or are used fictitiously.", styles['copyright']))
            story.append(Spacer(1, 4))
            story.append(Paragraph("First Edition: 2026", styles['copyright']))
            story.append(Paragraph("Printed in the United States of America", styles['copyright']))
        story.append(PageBreak())

        # === DEDICATION PAGE ===
        if self.dedication:
            story.append(Spacer(1, 200))
            story.append(Paragraph(self.dedication, styles['dedication']))
            story.append(PageBreak())

        # === EPIGRAPH PAGE ===
        if self.epigraph:
            story.append(Spacer(1, 180))
            story.append(Paragraph(self.epigraph, styles['epigraph']))
            if self.epigraph_attribution:
                story.append(Spacer(1, 8))
                story.append(Paragraph(f"\u2014 {self.epigraph_attribution}", styles['epigraph_attr']))
            story.append(PageBreak())

        # === TABLE OF CONTENTS ===
        story.append(Paragraph("CONTENTS", styles['toc_title']))
        story.append(Spacer(1, 10))
        for i, ch in enumerate(self.chapters):
            if i in self.part_titles:
                story.append(Spacer(1, 12))
                story.append(Paragraph(
                    f"<b>{self.part_titles[i]}</b>",
                    ParagraphStyle('toc_part', fontName='Times-Bold', fontSize=11,
                                   leading=16, alignment=TA_LEFT, leftIndent=10,
                                   textColor=GREY_TEXT)
                ))
                story.append(Spacer(1, 4))
            num_str = str(i + 1).rjust(2)
            story.append(Paragraph(
                f"{num_str}&nbsp;&nbsp;&nbsp;&nbsp;{ch['title']}",
                styles['toc_entry']
            ))
        story.append(PageBreak())

        # === BLANK PAGE before chapters ===
        story.append(Spacer(1, 1))
        story.append(PageBreak())

        # === CHAPTERS ===
        for i, ch in enumerate(self.chapters):
            # Part title page if applicable
            if i in self.part_titles:
                story.append(Spacer(1, 200))
                story.append(Paragraph(
                    self.part_titles[i].upper(),
                    styles['part_label']
                ))
                story.append(Spacer(1, 20))
                part_subtitle = self.part_titles[i]
                story.append(Paragraph(part_subtitle, styles['part_title']))
                story.append(PageBreak())

            # Chapter heading
            story.append(ChapterHeading(i + 1, ch['title'], self.style))
            story.append(Spacer(1, 20))

            # Chapter text
            paragraphs = ch['text'].split('\n\n')
            first = True
            for para_text in paragraphs:
                para_text = para_text.strip()
                if not para_text:
                    continue

                if para_text == '***' or para_text == '* * *':
                    story.append(Spacer(1, 6))
                    story.append(SectionBreak())
                    story.append(Spacer(1, 6))
                    first = True
                    continue

                # Escape XML special characters
                para_text = para_text.replace('&', '&amp;')
                para_text = para_text.replace('<', '&lt;')
                para_text = para_text.replace('>', '&gt;')

                # Restore italic/bold markers: use _text_ for italic, **text** for bold
                import re
                # Bold: **text**
                para_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', para_text)
                # Italic: _text_
                para_text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<i>\1</i>', para_text)

                if first:
                    story.append(Paragraph(para_text, styles['body_first']))
                    first = False
                else:
                    story.append(Paragraph(para_text, styles['body']))

            # Page break after each chapter
            story.append(PageBreak())

        # === END MATTER ===
        story.append(Spacer(1, 250))
        story.append(Paragraph("END", ParagraphStyle(
            'end', fontName='Times-Roman', fontSize=14, alignment=TA_CENTER,
            textColor=LIGHT_GREY
        )))

        # === BUILD PDF ===
        doc = BaseDocTemplate(
            output_path,
            pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
            title=self.title,
            author=self.author,
        )

        # Create frames for odd/even pages (mirrored margins for binding)
        frame_odd = Frame(
            MARGIN_INSIDE, MARGIN_BOTTOM,
            PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE,
            PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
            id='odd'
        )
        frame_even = Frame(
            MARGIN_OUTSIDE, MARGIN_BOTTOM,
            PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE,
            PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
            id='even'
        )

        # Page templates
        def _header_footer(canvas, doc):
            """Add running headers and page numbers."""
            canvas.saveState()
            page_num = doc.page

            # Skip headers/footers on early pages (front matter)
            if page_num <= 8:
                canvas.restoreState()
                return

            # Page number at bottom center
            canvas.setFont('Times-Roman', 9)
            canvas.setFillColor(GREY_TEXT)
            canvas.drawCentredString(PAGE_WIDTH / 2, MARGIN_BOTTOM - 20, str(page_num))

            # Running header
            if page_num > 10:
                canvas.setFont('Times-Italic', 8)
                canvas.setFillColor(LIGHT_GREY)
                if page_num % 2 == 0:
                    # Even page: author name on left
                    canvas.drawString(MARGIN_OUTSIDE, PAGE_HEIGHT - MARGIN_TOP + 15,
                                      self.author.upper())
                else:
                    # Odd page: book title on right
                    t = self.title.upper()
                    tw = canvas.stringWidth(t, 'Times-Italic', 8)
                    canvas.drawString(PAGE_WIDTH - MARGIN_OUTSIDE - tw,
                                      PAGE_HEIGHT - MARGIN_TOP + 15, t)

            canvas.restoreState()

        template = PageTemplate(
            id='main',
            frames=[frame_odd],
            onPage=_header_footer
        )

        doc.addPageTemplates([template])
        doc.build(story)
        print(f"Built: {output_path} ({doc.page} pages)")
        return doc.page


if __name__ == "__main__":
    # Quick test
    builder = BookBuilder("Test Book", "Test Author")
    builder.add_chapter("First Chapter", "This is a test paragraph.\n\nThis is another paragraph.\n\n***\n\nAfter the break.")
    builder.build("test_output.pdf")
