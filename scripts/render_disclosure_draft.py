"""Render the research response set; requires reportlab, outside core dependencies.

This creates a separate discussion PDF, never alters the original VIT form.
Run with the bundled document Python or an environment containing reportlab.
"""
from pathlib import Path
import re
import argparse
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted,
    KeepTogether, PageBreak,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/INVENTION_DISCLOSURE_B_CLAIMAUDIT_DRAFT.md'
OUTPUT = ROOT / 'output/pdf/ClaimAudit_IDF_B_Research_Draft.pdf'
INK = colors.HexColor('#16324F')
TEAL = colors.HexColor('#007F86')


def inline(text):
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # The response set contains plain URLs, rendered as clickable links.
    return re.sub(r'https://[^\s<>]+', lambda m: '<link href="' + m[0] + '">' + m[0] + '</link>', text)


def render(scope_v1=False):
    global SOURCE, OUTPUT
    if scope_v1:
        SOURCE = ROOT / "docs/INVENTION_DISCLOSURE_B_SCOPE_V1.md"
        OUTPUT = ROOT / "output/pdf/ClaimAudit_ScopeGuard_IDF_B.pdf"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyDraft', fontName='Helvetica', fontSize=10,
                              leading=14, spaceAfter=7, textColor=INK))
    styles.add(ParagraphStyle('SectionDraft', fontName='Helvetica-Bold', fontSize=13,
                              leading=17, spaceBefore=14, spaceAfter=7,
                              textColor=TEAL, keepWithNext=True))
    styles.add(ParagraphStyle('CellDraft', fontName='Helvetica', fontSize=8.2,
                              leading=11, textColor=INK, alignment=TA_LEFT))
    styles.add(ParagraphStyle('CodeDraft', fontName='Courier', fontSize=8,
                              leading=10, spaceAfter=9, textColor=INK))
    body = styles['BodyDraft']
    story = []
    lines = SOURCE.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('# '):
            story.append(Paragraph('CLAIMAUDIT', ParagraphStyle('Brand', fontSize=11,
                                   fontName='Helvetica-Bold', textColor=TEAL, spaceAfter=12)))
            story.append(Paragraph('Invention disclosure<br/>Research response draft',
                                   ParagraphStyle('TitleDraft', fontName='Helvetica-Bold',
                                   fontSize=25, leading=29, textColor=INK, spaceAfter=12)))
            story.append(Paragraph('Mapped to VIT IDF-B | ' + ('19 October 2026' if scope_v1 else '18 October 2026'), body))
        elif line.startswith('## '):
            if line == '## References' or re.match(r'## (3|4|7|8|9)\. ', line):
                story.append(PageBreak())
            story.append(Paragraph(inline(line[3:]), styles['SectionDraft']))
        elif line.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i])
                i += 1
            story.append(KeepTogether([Preformatted('\n'.join(code), styles['CodeDraft'])]))
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', c) for c in cells):
                    rows.append([Paragraph(inline(c), styles['CellDraft']) for c in cells])
                i += 1
            widths = [52*mm, 60*mm, 62*mm] if 'Prior art' in line else [94*mm, 40*mm, 40*mm]
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DCEEEF')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F4F7FA')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('LINEBELOW', (0, 0), (-1, 0), .6, TEAL),
            ]))
            story.extend([table, Spacer(1, 8)])
            continue
        elif line.startswith('- '):
            story.append(Paragraph(inline(line[2:]), body, bulletText='-'))
        else:
            paragraph = [line]
            while i+1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith(('#', '|', '-', '```')):
                i += 1
                paragraph.append(lines[i].strip())
            story.append(Paragraph(inline(' '.join(paragraph)), body))
        i += 1

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#C6D5DF'))
        canvas.line(18*mm, 17*mm, 192*mm, 17*mm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(INK)
        canvas.drawString(18*mm, 12*mm, 'DISCUSSION DRAFT | Novelty unresolved | ' + ('Bounded prototype implemented' if scope_v1 else 'Proposed extension not implemented'))
        canvas.drawRightString(192*mm, 12*mm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(OUTPUT), pagesize=(210*mm, 297*mm),
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=24*mm,
                            title='ClaimAudit - IDF-B Research Draft',
                            author='ClaimAudit research project')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope-v1", action="store_true")
    render(parser.parse_args().scope_v1)
