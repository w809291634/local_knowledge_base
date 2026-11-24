"""Read-only scan for authoring/evidence-access commentary accidentally written into PEMS body text."""
from pathlib import Path
import argparse,json,re,sys
from docx import Document
from docx.oxml.ns import qn
PATTERNS=[r'没有(?:源代码|源码)',r'(?:未提供|未取得|未获得|缺少).{0,8}(?:源代码|源码)',
          r'(?:基于|根据|依据|使用).{0,10}HEX.{0,10}(?:推测|推断|推导)',
          r'HEX.{0,16}(?:不足以证明|无法确认|不能证明|不能还原)',r'不能等同源码',r'不等同源码',
          r'经验库默认',r'本轮仅(?:取得|完成文档)',r'现场.{0,8}(?:未取得|未提供).{0,8}(?:源码|源代码)']
RX=re.compile('|'.join(PATTERNS),re.I)
def check(folder):
    files=sorted(Path(folder).glob('RD-*.docx'));errors=[]
    if not files:return ['没有匹配的PEMS文档']
    for path in files:
        d=Document(path)
        for i,p in enumerate(d.element.iter(qn('w:p'))):
            tx=''.join(e.text or '' for e in p.iter(qn('w:t')))
            if RX.search(tx):errors.append({'file':path.name,'paragraph':i,'text':tx})
    return errors
def main():
    ap=argparse.ArgumentParser();ap.add_argument('folder');ap.add_argument('--report');a=ap.parse_args()
    errors=check(a.folder);out={'pass':not errors,'files':len(list(Path(a.folder).glob('RD-*.docx'))),'errors':errors,'limit':'检查正文/表格/文本框中的作者取证说明；图内字须另外目检；源码管理/白盒测试等正常技术术语允许。'}
    if a.report:Path(a.report).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2));return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
