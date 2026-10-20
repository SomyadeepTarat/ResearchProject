"""Render the reviewed memo and completed IDF-B; requires ReportLab."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, PageBreak
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/adversarial_review'; OUT=ROOT/'output/pdf'
INK=colors.HexColor('#18354A'); TEAL=colors.HexColor('#006B70')

def clean(s):
    for x in ('—','–','‑'): s=s.replace(x,'-')
    return s.replace('“','"').replace('”','"').replace('’',"'").replace('→','->')

def inline(s):
    s=escape(clean(s)).replace('&lt;br&gt;','<br/>')
    return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)

class Diagram(Flowable):
    def __init__(self):
        super().__init__(); self.width=475; self.height=202
    def draw(self):
        c=self.canv
        boxes=[(0,142,145,44,'Reviewed facts + predicates','Explicit context + source'),(165,142,145,44,'Categorical alternatives','Exactly one per block'),(330,142,145,44,'Boolean lineage','Context-coherent predicates'),(165,64,145,44,'Compile once: BDD','Restrict each clarification'),(330,64,145,44,'Verdict + outcomes','Known BDD operations'),(0,0,475,38,'Cross-check same policy: ProbLog/PySDD | Z3 SMT | exhaustive enumeration','No automatic PDF extraction; no new algorithm claimed')]
        for x,y,w,h,a,b in boxes:
            c.setFillColor(colors.HexColor('#EFF5F5'));c.setStrokeColor(TEAL);c.roundRect(x,y,w,h,5,fill=1)
            c.setFillColor(INK);c.setFont('Helvetica-Bold',8);c.drawCentredString(x+w/2,y+h-15,a)
            c.setFont('Helvetica',7.5);c.drawCentredString(x+w/2,y+10,b)
        for x1,y1,x2,y2 in [(145,164,165,164),(310,164,330,164),(402,142,237,108),(310,86,330,86),(237,64,237,38)]:
            c.setStrokeColor(TEAL);c.line(x1,y1,x2,y2)
            if y1==y2: c.line(x2-4,y2-3,x2,y2);c.line(x2-4,y2+3,x2,y2)
            else: c.line(x2-3,y2+5,x2,y2);c.line(x2+3,y2+5,x2,y2)

class TRL(Flowable):
    def __init__(self):
        super().__init__(); self.width=475; self.height=48
    def draw(self):
        c=self.canv
        for i in range(1,10):
            x=(i-1)*53
            c.setStrokeColor(TEAL if i==3 else colors.gray);c.rect(x,22,12,12)
            if i==3:
                c.setLineWidth(2);c.line(x+2,28,x+5,25);c.line(x+5,25,x+10,32);c.setLineWidth(1)
            c.setFillColor(INK);c.setFont('Helvetica-Bold' if i==3 else 'Helvetica',8);c.drawString(x,8,f'TRL {i}')

def footer(c,doc):
    c.setStrokeColor(colors.HexColor('#CDDADA'));c.line(48,42,A4[0]-48,42)
    c.setFont('Helvetica',8);c.setFillColor(INK)
    c.drawString(48,29,'ClaimAudit / ScopeGuard | Research assessment | No established novelty')
    c.drawRightString(A4[0]-48,29,str(doc.page))

def render(source,target,memo=False):
    body=ParagraphStyle('body',fontName='Helvetica',fontSize=10.3 if memo else 10,leading=14,spaceAfter=7,textColor=INK)
    title=ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=18 if memo else 21,leading=22 if memo else 26,spaceAfter=12,textColor=INK)
    section=ParagraphStyle('section',fontName='Helvetica-Bold',fontSize=12,leading=16,spaceBefore=12,spaceAfter=8,textColor=TEAL,keepWithNext=True)
    cell=ParagraphStyle('cell',fontName='Helvetica',fontSize=8,leading=10.5,textColor=INK,spaceAfter=2,splitLongWords=True)
    story=[]; lines=source.read_text().splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('# '):story.append(Paragraph(inline(line[2:]),title))
        elif line.startswith('## '):
            # Prior-art register begins on its own page; subsequent answers resume after it.
            if line.startswith('## 3.') or line.startswith('## 4.') or line.startswith('## 8.') or line.startswith('## 7.'):
                story.append(PageBreak())
            story.append(Paragraph(inline(line[3:]),section))
        elif line=='[DIAGRAM]':story.append(Diagram());story.append(Spacer(1,8))
        elif line=='[TRL_CHECKBOXES]':story.append(TRL())
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                bits=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',x) for x in bits):rows.append([Paragraph(inline(x),cell) for x in bits])
                i+=1
            widths=[230,245] if len(rows[0])==2 else [97,113,140,125]
            table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDEDEE')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),0.4,colors.HexColor('#BCD0D2')),('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#BCD0D2')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.append(table);story.append(Spacer(1,8));continue
        else:story.append(Paragraph(inline(line),body))
        i+=1
    OUT.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(target),pagesize=A4,rightMargin=54,leftMargin=54,topMargin=43 if memo else 48,bottomMargin=54,title=source.stem,author='ClaimAudit research assessment').build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':
    render(D/'STAGE2_DECISION_MEMO.md',OUT/'ClaimAudit_Novelty_Decision_Memo.pdf',True)
    render(D/'STAGE4_COMPLETED_IDF_B.md',OUT/'ClaimAudit_IDF_B_Adversarial_Review.pdf')
