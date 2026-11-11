from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
from collections import Counter
import csv, re, json, hashlib, ast, html

TASK=Path(__file__).parent
ROOT=Path(r'C:\CHI3242文本發掘\第二次作業')
REF=Path(r'C:\CHI3242文本發掘\第一次作業\Report.docx')
OUT=TASK/'stage'; OUT.mkdir(exist_ok=True)
def readcsv(p): return list(csv.DictReader(p.open(encoding='utf-8-sig')))
sources=readcsv(ROOT/'data/v3/sources.csv'); sentences=readcsv(ROOT/'data/v3/sentences_all.csv'); main=readcsv(ROOT/'data/v3/dataset_v3.csv')
assert len(sources)==70 and len({s['work_id'] for s in sources})==70
assert len(main)==1163 and sum(s['trainable']=='True' for s in sentences)==1654
rawc=Counter(s['work_id'] for s in sentences)
fullc=Counter(s['work_id'] for s in sentences if s['trainable']=='True')
mainc=Counter(s['work_id'] for s in main)
trc=Counter(s['work_id'] for s in main if s['split']=='train')
tec=Counter(s['work_id'] for s in main if s['split']=='test')
assert len(fullc)==52 and len(mainc)==52
rows=[]
for s in sources:
 i=s['work_id']; spec=ast.literal_eval(s['extract_spec'] or '{}'); mode=s['extract_mode']
 if mode=='whole': scope='全篇'
 elif mode=='section': scope='指定篇章全文：'+spec['section']
 elif mode in ('paragraphs','section_paragraphs'):
  scope=('指定篇章「'+spec['section']+'」內' if mode=='section_paragraphs' else '底本內')+'選段 '+ '、'.join(map(str,spec['indices']))+'（從0起）'
 elif mode=='non_shu_section': scope='「'+spec['section']+'」；依程式排除以疏、正義曰等開頭的行'
 else: scope='未擷取正文'
 if rawc[i]==0: scope='未擷取正文；目錄候選，非實際語料'
 state=('主樣本' if mainc[i] else {'reserved':'整篇留出應用','uncertain':'歸屬待核','uncertain_attribution':'歸屬待核','pending':'待核未收','excluded':'未收'}.get(s['status'],'未取樣'))
 note=s['notes']
 if i=='P02': state='候選別名記錄';note+='；實際納入條目為E37，本筆不重複計篇或計句。'
 if i=='P03': state='候選別名記錄';note+='；實際納入條目為E39，本筆不重複計篇或計句。'
 if i=='P01': state='候選作者總目';note+='；本筆是一組候選作者，並非一篇作品，不與其下另收的篇章重複計數。'
 title=s['work_title']
 if i=='E04':title+='（節選）'
 if i=='W25':title='移書讓太常博士（所據條目全文，並序）'
 period='歸屬待核' if s['status'] in ('uncertain','uncertain_attribution') else s['period']
 rows.append(dict(編號=i,分期=period,作者=(s['author']+'（舊題）' if i in ('W17','W18') else s['author']),篇名=title,收錄範圍=scope,底本=s['base_page'] or '未固定',修訂號=s['base_revision'] or '未固定',底本網址=s['base_url'],固定修訂網址=('https://zh.wikisource.org/w/index.php?oldid='+s['base_revision']) if s['base_revision'] else '',候選句=rawc[i],可建模全庫句=fullc[i],主樣本句=mainc[i],訓練句=trc[i],測試句=tec[i],用途=state,分期依據=s['dating_basis'],選篇依據=s['cao_section'],曹本頁碼狀態='據線上目錄，待核原書',說明=note))
with (OUT/'corpus_catalogue.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

body=(TASK/'body.md').read_text(encoding='utf8')
visible=re.sub(r'^\|[-:|]+\|$','',body,flags=re.M);visible=re.sub(r'[#*|\s]','',visible)
counts={'正文可見非空白字元含標點表格標題':len(visible),'正文漢字':len(re.findall(r'[\u3400-\u9fff]',visible))}
assert 2000<=counts['正文漢字']<=2500 and 2000<=len(visible)<=2500,counts
refs='''## 參考書目

曹順慶主編：《兩漢文論譯注》，北京：北京出版社，1988。選篇據線上目錄，未據原書核頁。

嚴可均輯：《全上古三代秦漢三國六朝文》所收《全漢文》《全後漢文》。本文實際採維基文庫電子轉錄，中華書局影印本頁碼未核。

揚雄：《法言》〈吾子〉；班固：《漢書》卷三十〈藝文志〉；王充：《論衡》〈藝增〉、〈超奇〉。固定修訂號及全庫篇目見附錄與corpus_catalogue.csv。

Zádrapa, Lukáš. “A Report on Stylometric Experiments with Pre-Modern Chinese Texts.” Archiv orientální 92, no. 1 (2024): 109–127. https://doi.org/10.47979/aror.j.92.1.109-127

Sturgeon, Donald. “Unsupervised Identification of Text Reuse in Early Chinese Literature.” Digital Scholarship in the Humanities 33, no. 3 (2018): 670–684. https://doi.org/10.1093/llc/fqx024

Pines, Yuri. “Dating a Pre-imperial Text: The Case Study of the Book of Lord Shang.” Early China 39 (2016): 145–184. https://doi.org/10.1017/eac.2016.3

馬傑：CHI3242作業二及課程網站。https://mcjkurz.github.io/teaching/courses/2026-2027/CHI3242/assignments/assignment-2/

## 研究流程與AI使用說明

研究問題、選材方向與〈超奇〉才具及文實關係的初步判讀由作者提出。VS Code中的AI協助整理語料、編程與執行分析；Codex協助核對數字、查找及整理研究文獻、草擬文字與排版。本稿供作者審閱，未將自動核對視為逐篇人工校勘。
'''
intro='''## 附錄　語料全目與計數說明

本附錄列盡來源表七十筆編號記錄，並非七十篇獨立作品。實際保存句資料的有五十六筆：五十二個可建模篇章單位、〈超奇〉一篇，以及三筆歸屬待核材料；其餘十四筆是未擷取的候選或不收記錄，其中含別名及作者總目。來源表的舊狀態文字不替代實際句表，本附錄以逐句記錄彙總用途和數量。

「候選／全庫」分別為保存的切句數與可建模句數；「主樣本／訓練／測試」為限額取樣後的三項句數。全庫不含整篇留出與歸屬待核材料。候選1888句＝可建模篇章原始1700句＋〈超奇〉129句＋歸屬待核59句；1700句經篩選得1654句，再取1163句，分930句訓練、233句測試。未擷取記錄的0只表示未進入句表，不表示原作無文字。

西漢可建模21個篇章單位、7位作者；東漢31個篇章單位、8位作者。表內同一作者的不同篇章分列，同一篇的多句不另計篇。W、E編號是追溯鍵，歸屬待核的W17、W18不因編號而認定為西漢。

各表使用一致欄位；底本後括號為維基文庫固定修訂號，可用https://zh.wikisource.org/w/index.php?oldid=加該號回查。節選段號按擷取程式的非空白行序列從0起算，非原書段次或頁碼；連續及不連續選段均列出。曹本僅為選篇依據，實際輸入底本以本表為準。完整網址、分期依據及選篇說明另存corpus_catalogue.csv。

〈自紀〉實為節選；〈移書讓太常博士〉原資料題名雖標節選，程式實取所據條目全文並序，表中據實標明。全篇指所據電子條目的範圍，不保證其中沒有附序、輯佚痕跡或後人引入語；這些層次仍須人工校勘。P02、P03是E37、E39的候選別名記錄，均不重複計數。候選總目P01亦不作單篇計數。
'''
groups=[('甲　西漢可建模語料',[r for r in rows if r['可建模全庫句'] and r['分期']=='西漢']),('乙　東漢可建模語料',[r for r in rows if r['可建模全庫句'] and r['分期']=='東漢']),('丙　整篇留出與歸屬待核',[r for r in rows if r['候選句'] and not r['可建模全庫句']]),('丁　未擷取及不收的來源記錄',[r for r in rows if not r['候選句']])]
def table_cells(r):
 return [r['編號'],r['作者']+'：'+r['篇名'],r['收錄範圍']+'；底本：'+r['底本']+'（'+r['修訂號']+'）',f"{r['候選句']}／{r['可建模全庫句']}",f"{r['主樣本句']}／{r['訓練句']}／{r['測試句']}",r['用途']]
headers=['編號','作者與篇名','收錄範圍及底本','候選／全庫','主／訓／測','用途']
appendix=intro
for heading,rr in groups:
 appendix+='\n### '+heading+'\n\n|'+'|'.join(headers)+'|\n|'+'|'.join(['---']*6)+'|\n'
 for r in rr: appendix+='|'+'|'.join(table_cells(r))+'|\n'
final=body+'\n'+refs+'\n'+appendix
(OUT/'report.md').write_text(final,encoding='utf8')
(OUT/'corpus_catalogue.md').write_text(appendix,encoding='utf8')

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';ns={'w':W}
def tag(x): return '{'+W+'}'+x
with ZipFile(REF) as z: parts={n:z.read(n) for n in z.namelist()}
doc=E.fromstring(parts['word/document.xml']); b=doc.find('w:body',ns)
ps=b.findall('w:p',ns); section=deepcopy(b.find('w:sectPr',ns)); templates={'title':deepcopy(ps[0]),'subtitle':deepcopy(ps[1]),'head':deepcopy(ps[2]),'text':deepcopy(ps[3]),'caption':deepcopy(ps[7]),'ref':deepcopy(ps[32])}
table_template=deepcopy(b.findall('w:tbl',ns)[1])
for c in list(b): b.remove(c)
def paragraph(text,kind='text',break_before=False):
 p=deepcopy(templates[kind]);pr=p.find('w:pPr',ns)
 if pr is None:pr=E.Element(tag('pPr'));p.insert(0,pr)
 for c in list(p):
  if c is not pr:p.remove(c)
 if break_before:E.SubElement(pr,tag('pageBreakBefore'))
 if text.startswith('其文獻學意義'):E.SubElement(pr,tag('keepLines'))
 r=E.SubElement(p,tag('r'))
 if kind=='title':
  rp=E.SubElement(r,tag('rPr'));E.SubElement(rp,tag('sz')).set(tag('val'),'28')
 E.SubElement(r,tag('t')).text=text
 b.append(p);return p
def table(data,widths):
 t=deepcopy(table_template)
 for c in list(t):
  if c.tag==tag('tr'):t.remove(c)
 grid=t.find('w:tblGrid',ns)
 for c in list(grid):grid.remove(c)
 for wi in widths:E.SubElement(grid,tag('gridCol')).set(tag('w'),str(wi))
 pr=t.find('w:tblPr',ns)
 for e in pr.findall('w:tblW',ns):e.set(tag('w'),str(sum(widths)));e.set(tag('type'),'dxa')
 for j,row in enumerate(data):
  tr=E.SubElement(t,tag('tr'));trpr=E.SubElement(tr,tag('trPr'));E.SubElement(trpr,tag('cantSplit'))
  if j==0:E.SubElement(trpr,tag('tblHeader'))
  for k,txt in enumerate(row):
   tc=E.SubElement(tr,tag('tc'));cp=E.SubElement(tc,tag('tcPr'));tw=E.SubElement(cp,tag('tcW'));tw.set(tag('w'),str(widths[k]));tw.set(tag('type'),'dxa')
   E.SubElement(cp,tag('vAlign')).set(tag('val'),'center')
   if j==0:E.SubElement(cp,tag('shd')).set(tag('fill'),'F2F2F2')
   borders=E.SubElement(cp,tag('tcBorders'))
   for side in ['top','left','bottom','right']:
    el=E.SubElement(borders,tag(side));el.set(tag('val'),'single');el.set(tag('sz'),'4');el.set(tag('color'),'D9D9D9')
   mar=E.SubElement(cp,tag('tcMar'))
   for side in ['top','bottom','left','right']:
    el=E.SubElement(mar,tag(side));el.set(tag('w'),'65');el.set(tag('type'),'dxa')
   p=E.SubElement(tc,tag('p'));pp=E.SubElement(p,tag('pPr'));E.SubElement(pp,tag('spacing')).set(tag('after'),'0')
   if j==0:E.SubElement(pp,tag('keepNext'))
   E.SubElement(pp,tag('jc')).set(tag('val'),'left' if k in [1,2,5] and data[0][0]=='編號' else 'center')
   r=E.SubElement(p,tag('r'));rp=E.SubElement(r,tag('rPr'));E.SubElement(rp,tag('sz')).set(tag('val'),'20')
   if j==0:E.SubElement(rp,tag('b'))
   E.SubElement(r,tag('t')).text=txt
 b.append(t)
current_table=[]; paragraphs={}; inrefs=False
def flush():
 global current_table
 if current_table:
  table(current_table,[1660]*5 if len(current_table[0])==5 else [1350,1400,1400,1300,1400,1450]);current_table=[]
for line in (body+'\n'+refs).splitlines():
 if line.startswith('|'):
  if not re.match(r'^\|[-:|]+\|$',line):current_table.append([c.strip() for c in line.strip('|').split('|')])
  continue
 flush()
 if not line:continue
 if line.startswith('# '):paragraph(line[2:],'title')
 elif line.startswith('## ——'):paragraph(line[3:],'subtitle')
 elif line.startswith('## '):
  isref=line=='## 參考書目';paragraph(line[3:],'head');inrefs=isref or inrefs
 elif line.startswith('**'):paragraph(line.strip('*'),'caption')
 else:paragraphs[line]=paragraph(line,'ref' if inrefs and not line.startswith('研究問題、') else 'text')
flush()
# Short source footnotes, replacing the reference essay's notes.
notes=[('揚雄說','揚雄：《法言》〈吾子〉，維基文庫固定修訂2269064；班固：《漢書》卷三十，固定修訂7908197。逐句定位為W06-015、E11-018。'),('主模型判對','主結果據output/v3/metrics.json與test_predictions.csv；同文類、篇章及跨作者對照分別見genre_experiment、grouped、author_pairings資料夾。版本沿革及重跑指令保留於工程記錄。'),('〈論衡·藝增〉說','王充：《論衡》〈藝增〉，原文及兩種模型判向見E05-001；固定底本見附錄E05。'),('再讀整篇留出的','王充：《論衡》〈超奇〉，維基文庫固定修訂2326276。兩處定位E01-014、E01-047；預測據output/v3/independent_predictions.csv。')]
foot=E.fromstring(parts['word/footnotes.xml'])
ft=next(deepcopy(f) for f in foot if f.get(tag('id'))=='1')
for f in list(foot):
 if int(f.get(tag('id'))) > 0:foot.remove(f)
for i,(start,txt) in enumerate(notes,1):
 p=next(p for text,p in paragraphs.items() if text.startswith(start))
 r=E.SubElement(p,tag('r'));rp=E.SubElement(r,tag('rPr'));E.SubElement(rp,tag('vertAlign')).set(tag('val'),'superscript');E.SubElement(r,tag('footnoteReference')).set(tag('id'),str(i))
 f=E.SubElement(foot,tag('footnote'));f.set(tag('id'),str(i));p=E.SubElement(f,tag('p'));pp=E.SubElement(p,tag('pPr'))
 oldpr=ft.find('w:p/w:pPr',ns)
 if oldpr is not None:p.remove(pp);p.append(deepcopy(oldpr))
 r=E.SubElement(p,tag('r'));E.SubElement(r,tag('footnoteRef'));r=E.SubElement(p,tag('r'));E.SubElement(r,tag('t')).text=' '+txt
for line in intro.splitlines():
 if line.startswith('## '):paragraph(line[3:],'head',True)
 elif line:paragraph(line)
for heading,rr in groups:
 paragraph(heading,'head')
 table([headers]+[table_cells(r) for r in rr],[550,2050,3000,850,1000,850])
b.append(section)
parts['word/document.xml']=E.tostring(doc,encoding='UTF-8',xml_declaration=True,standalone=True)
parts['word/footnotes.xml']=E.tostring(foot,encoding='UTF-8',xml_declaration=True,standalone=True)
# Clear inherited authorship metadata and obsolete counts without touching styles.
core=E.fromstring(parts['docProps/core.xml'])
for x in core:
 if E.QName(x).localname in ('creator','lastModifiedBy','title','subject','description'):x.text=''
parts['docProps/core.xml']=E.tostring(core,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(OUT/'report.docx','w',ZIP_DEFLATED) as z:
 for n,v in parts.items():z.writestr(n,v)
# Standalone HTML shares the same complete manuscript and catalogue.
elems=[];tb=False
for line in final.splitlines():
 if line.startswith('|'):
  if re.match(r'^\|[-:|]+\|$',line):continue
  if not tb:elems.append('<div class="tablewrap"><table>');tb=True;cell='th'
  else:cell='td'
  elems.append('<tr>'+''.join(f'<{cell}>'+html.escape(c.strip())+f'</{cell}>' for c in line.strip('|').split('|'))+'</tr>');continue
 if tb:elems.append('</table></div>');tb=False
 if not line:continue
 if line.startswith('#'):
  level=len(line)-len(line.lstrip('#'));elems.append(f'<h{level}>'+html.escape(line[level:].strip())+f'</h{level}>')
 else:elems.append('<p>'+html.escape(line.strip('*'))+'</p>')
if tb:elems.append('</table></div>')
css='body{max-width:860px;margin:48px auto;padding:0 24px;color:#111;font:18px/1.65 "PMingLiU","Noto Serif TC",serif}h1{text-align:center;font-size:26px;font-weight:normal}h2{font-size:21px;font-weight:normal;margin-top:32px}h3{font-size:19px}p{text-indent:2em}table{border-collapse:collapse;width:100%;font-size:15px;line-height:1.45}td,th{border:1px solid #d9d9d9;padding:7px;vertical-align:middle}th{background:#f2f2f2}.tablewrap{overflow-x:auto}@media print{body{font-size:12pt;margin:0}h2,h3{break-after:avoid}tr{break-inside:avoid}}'
(OUT/'report.html').write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>詞語與兩漢文論的時期歸屬</title><style>'+css+'</style><body>'+''.join(elems)+'</body></html>',encoding='utf8')
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [REF,ROOT/'data/v3/sources.csv',ROOT/'data/v3/sentences_all.csv',ROOT/'data/v3/dataset_v3.csv',ROOT/'output/v3/metrics.json']}
audit={'counts':counts,'records':70,'groups':[(h,len(rr)) for h,rr in groups],'candidate_sentences':sum(rawc.values()),'full_sentences':sum(fullc.values()),'main_sentences':sum(mainc.values()),'train':sum(trc.values()),'test':sum(tec.values()),'input_hashes':hashes,'preserved_parts':[n for n in parts if n not in ['word/document.xml','word/footnotes.xml','docProps/core.xml']]}
(TASK/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
(TASK/'artifact.md').write_text('Reference: '+str(REF)+'\nSHA256: '+hashes[str(REF)]+'\n8 pages, 1 section. A4 210x297mm; margins top/bottom25.4mm left/right31.75mm. Normal Times New Roman / 新細明體 12pt black, first-line24pt, line1.3, after6pt. Title14pt centered, subtitle centered12pt; headings preserve source style and 1.5 line spacing. Tables grey borders/shaded header,10pt; right-aligned PAGE footer. Content slots: replace essay, two tables, bibliography, AI disclosure and all source-specific footnotes; expand appendix tables using same visual design. Preserve all other package parts, section geometry and styles. Full rewrite changes text flow, not fixed page count. Source footnotes replaced with four relevant short citations. Renderer unavailable due missing LibreOffice; use native Word PDF export and Poppler full-page inspection.\n',encoding='utf8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
