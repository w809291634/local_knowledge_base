"""Read-only template-header presence/identity/structure gate. See the PEMS format master."""
from pathlib import Path
import argparse,json,re,sys
from docx import Document
from docx.oxml.ns import qn

def text(header):return ''.join(e.text or '' for e in header._element.iter(qn('w:t')))
def norm(value):return re.sub(r'\s+','',value)
def style_border_count(header):
    count=0
    for p in header.paragraphs:
        style=p.style;seen=set()
        while style is not None and style.style_id not in seen:
            seen.add(style.style_id);count+=len(style.element.findall('.//'+qn('w:pBdr')));style=style.base_style
    return count
def expected(template,code):
    for s in template.sections:
        for h in [s.header,s.first_page_header,s.even_page_header]:
            m=re.search(r'QR/RD/'+re.escape(code)+r'\s+(\d+(?:\.\d+)+)',text(h))
            if m:return 'QR/RD/'+code,m[1]
    raise ValueError('Template has no confirmed document code/version: '+code)

def check(folder,map_path,pdf_dir=None):
    specs=json.loads(Path(map_path).read_text(encoding='utf-8'));files=sorted(Path(folder).glob('RD-*.docx'))
    errors=[];records=[]
    if not files:return ['No matching documents'],records
    for path in files:
        code=path.name[3:6]
        if code not in specs:errors.append(path.name+': missing explicit template map');continue
        src=Document(specs[code]['path']);doc=Document(path);ident,version=expected(src,code)
        if len(src.sections)!=len(doc.sections):errors.append(path.name+': section count differs')
        even=doc.settings.element.find(qn('w:evenAndOddHeaders')) is not None
        for i,s in enumerate(doc.sections):
            variants=[('default',s.header)]
            if s.different_first_page_header_footer:variants.append(('first',s.first_page_header))
            if even:variants.append(('even',s.even_page_header))
            for kind,h in variants:
                got=norm(text(h));want=norm(ident+version)
                if want not in got:errors.append(f'{path.name} section {i+1} {kind}: missing {ident} {version}')
                if i<len(src.sections):
                    baseline=getattr(src.sections[i],{'default':'header','first':'first_page_header','even':'even_page_header'}[kind])
                    if not norm(text(baseline)):baseline=src.sections[0].header
                    if [p.style.name for p in h.paragraphs]!=[p.style.name for p in baseline.paragraphs]:errors.append(f'{path.name} section {i+1}: template header paragraph styles changed')
                    if style_border_count(h)<style_border_count(baseline):errors.append(f'{path.name} section {i+1}: template header rule/border style lost')
                    for tag in ['w:tbl','w:drawing','w:pict','w:pBdr']:
                        if len(h._element.findall('.//'+qn(tag)))<len(baseline._element.findall('.//'+qn(tag))):errors.append(f'{path.name} section {i+1}: header lost {tag}')
                records.append({'file':path.name,'section':i+1,'kind':kind,'expected_code':ident,'expected_version':version,'actual':text(h)})
        if pdf_dir:
            import fitz
            pdf=Path(pdf_dir)/(path.stem+'.pdf')
            if not pdf.exists():errors.append(path.name+': PDF missing');continue
            with fitz.open(pdf) as rendered:
                for j,page in enumerate(rendered):
                    got=norm(page.get_text(clip=fitz.Rect(0,0,page.rect.width,page.rect.height*.1)))
                    if norm(ident+version) not in got:errors.append(f'{path.name} PDF page {j+1}: template header/version not visible')
    return errors,records

def main():
    ap=argparse.ArgumentParser();ap.add_argument('folder');ap.add_argument('--map',required=True);ap.add_argument('--pdf');ap.add_argument('--report')
    a=ap.parse_args();errors,records=check(a.folder,a.map,a.pdf)
    out={'pass':not errors,'documents':len(set(r['file'] for r in records)),'headers_checked':len(records),'errors':errors,'records':records}
    if a.report:Path(a.report).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='records'},ensure_ascii=False,indent=2));return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
