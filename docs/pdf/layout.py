from pathlib import Path
from html import escape
from urllib.parse import quote
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf'
OUT.mkdir(parents=True,exist_ok=True)
NAVY = colors.HexColor('#132B43')
TEAL = colors.HexColor('#007F82')
LIGHT = colors.HexColor('#EDF5F6')
GRAY = colors.HexColor('#52616F')
LINE = colors.HexColor('#D9E2E8')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCustom', fontName='Helvetica-Bold', fontSize=29, leading=33, textColor=NAVY, spaceAfter=17))
styles.add(ParagraphStyle(name='Section', fontName='Helvetica-Bold', fontSize=21, leading=25, textColor=NAVY, spaceAfter=13))
styles.add(ParagraphStyle(name='Sub', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=TEAL, spaceBefore=11, spaceAfter=5))
styles.add(ParagraphStyle(name='TextCustom', fontName='Helvetica', fontSize=10.5, leading=15, textColor=NAVY, spaceAfter=8))
styles.add(ParagraphStyle(name='SmallCustom', fontName='Helvetica', fontSize=8.5, leading=12, textColor=GRAY, spaceAfter=6))
styles.add(ParagraphStyle(name='Cell', fontName='Helvetica', fontSize=9.3, leading=13, textColor=NAVY))
styles.add(ParagraphStyle(name='CodeCustom', fontName='Courier', fontSize=8.1, leading=11.5, textColor=NAVY, backColor=LIGHT, borderPadding=10, spaceBefore=7, spaceAfter=10))

def p(text, style='TextCustom'):
    return Paragraph(text, styles[style])

def sub(text):
    return p(text, 'Sub')

def code(text):
    return Preformatted(text.strip(), styles['CodeCustom'])

def callout(label, text):
    t = Table([[p(label, 'Sub')], [p(text)]], colWidths=[483])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('BOX',(0,0),(-1,-1),0.5,LINE),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,0),2),('BOTTOMPADDING',(0,-1),(-1,-1),6)]))
    return t

def table(headers, rows, widths):
    data = [[p('<b>'+escape(x)+'</b>', 'Cell') for x in headers]]
    data += [[p(x,'Cell') for x in row] for row in rows]
    t=Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.8,TEAL),('LINEBELOW',(0,1),(-1,-1),0.4,LINE),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t


from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
font_root = Path('/System/Library/Fonts/Supplemental')
if font_root.exists():
    font_files = [font_root/name for name in ('Arial.ttf','Arial Bold.ttf','Arial Italic.ttf')]
else:
    font_root = Path(reportlab.__file__).parent/'fonts'
    font_files = [font_root/name for name in ('Vera.ttf','VeraBd.ttf','VeraIt.ttf')]
pdfmetrics.registerFont(TTFont('DocArial', str(font_files[0])))
pdfmetrics.registerFont(TTFont('DocArialBold', str(font_files[1])))
pdfmetrics.registerFont(TTFont('DocArialItalic', str(font_files[2])))
pdfmetrics.registerFontFamily('DocArial', normal='DocArial', bold='DocArialBold', italic='DocArialItalic', boldItalic='DocArialBold')

for name in ['TextCustom','SmallCustom','Cell']:
    styles[name].fontName='DocArial'
for name in ['TitleCustom','Section','Sub']:
    styles[name].fontName='DocArialBold'
styles['TextCustom'].fontSize=10.5
styles['TextCustom'].leading=15.2
styles['Sub'].textColor=NAVY
styles['Sub'].fontSize=11.5
styles['Sub'].spaceBefore=12
styles['Section'].fontSize=20
styles['Section'].leading=25
styles['SmallCustom'].fontSize=8.6
styles['SmallCustom'].leading=12



def heading(title):
    return p('<font color="#168CAE">&gt;</font> <font color="#18875B">&gt;</font> <font color="#C53D60">&gt;</font> '+title, 'Section')

def section(kicker,title,*body):
    return [p(kicker.upper(),'SmallCustom'), heading(title), *body]

def build(filename,pages):
    blocks=pages
    titles=[b[1].getPlainText().replace('> > > ','') for b in blocks]
    story=[]
    for i,block in enumerate(blocks):
        if i:story.append(PageBreak())
        story.extend(block)
    def decorate(c,doc):
        c.saveState()
        c.setFont('DocArial',8); c.setFillColor(GRAY)
        c.drawString(56,813,'PROJECT FARO / ASK YOUR TERMINAL DATA')
        c.setStrokeColor(LINE);c.line(56,805,539,805)
        c.line(56,42,539,42)
        c.drawString(56,29,'DELIVERY PROPOSAL')
        c.drawRightString(539,29,f'{doc.page} / {len(blocks)}')
        if doc.page <= len(titles):
            key='page-'+str(doc.page)
            c.bookmarkPage(key);c.addOutlineEntry(titles[doc.page-1],key,level=0,closed=False)
        c.restoreState()
    doc=SimpleDocTemplate(str(OUT/filename),pagesize=(595.28,841.89),leftMargin=56,rightMargin=56,topMargin=53,bottomMargin=57,
        title='Project Faro - terminal data service proposal',author='Ruddi Rodriguez Garcia',subject='Architecture, processing logic, edge cases, cost, testing and client value')
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)

class ServiceCircle(Flowable):
    def __init__(self):
        super().__init__(); self.width=483; self.height=325
    def draw(self):
        from math import hypot,atan2,cos,sin
        c=self.canv; cx,cy=241.5,157; r=57
        def link(x,y):
            dx,dy=x-cx,y-cy; d=hypot(dx,dy)
            a,b=cx+r*dx/d,cy+r*dy/d
            c.setStrokeColor(TEAL);c.line(a,b,x,y)
            for ex,ey,ang in [(x,y,atan2(dy,dx)),(a,b,atan2(-dy,-dx))]:
                for s in [-1,1]: c.line(ex,ey,ex-4*cos(ang+s*.5),ey-4*sin(ang+s*.5))
        def box(x,y,title,detail):
            c.setFillColor(LIGHT);c.setStrokeColor(LINE)
            c.roundRect(x,y,145,43,5,fill=1,stroke=1)
            c.setFillColor(NAVY);c.setFont('DocArialBold',9);c.drawCentredString(x+72.5,y+27,title)
            c.setFont('DocArial',8);c.drawCentredString(x+72.5,y+12,detail)
        nodes=[(0,247,'Gate','Checks who may see what'),(338,247,'Library','Holds company meanings'),
               (0,187,'Thread','Combines question and replies'),(338,187,'Scout','Finds relevant company text'),
               (0,104,'Signal','Decides: continue, ask, or stop'),(338,104,'Guide','Writes a follow-up question'),
               (0,44,'Bridge / Shield','Gets facts / checks them'),(338,44,'Voice','Explains supported results')]
        for x,y,t,d in nodes:
            link(145 if x==0 else 338,y+21.5);box(x,y,t,d)
        c.setFillColor(NAVY);c.circle(cx,cy,r,fill=1,stroke=0)
        c.setFillColorRGB(1,1,1);c.setFont('DocArialBold',12);c.drawCentredString(cx,cy+13,'COMPASS')
        c.setFont('DocArial',8.5);c.drawCentredString(cx,cy-3,'Coordinates the services')
        c.drawCentredString(cx,cy-17,'Calls the next service')
        c.setFillColor(NAVY);c.setFont('DocArialBold',10)
        c.drawCentredString(cx,311,'Maria’s screen: sign in, ask, reply, read the answer')
        c.setFont('DocArial',8);c.drawCentredString(cx,20,'Connector: opens permitted files for Scout, Bridge and Shield.')
        c.drawCentredString(cx,7,'Compass keeps the question, evidence and answer together in the company’s collection.')