"""Check the wording of PEMS Word files. Raster diagrams require visual review."""
import argparse,json,re,sys,zipfile
from pathlib import Path
from lxml import etree

MATERIAL=r'(?:源码|源代码|原理图|BOM|工程配置|编译工程|构建记录|测试记录|试验记录|实测数据|原始记录|设计输入|设计文件|接口定义|技术要求|说明书|资料|材料)'
GAP=r'(?:没有|未提供|未取得|未获得|未能获取|缺少|缺乏|缺失|无法取得|尚未取得|仅取得)'
INFERENCE=r'(?:推测|推断|反推|猜测|推导)'
PATTERNS={
 '作者取证说明':rf'{GAP}.{{0,12}}{MATERIAL}|{MATERIAL}.{{0,9}}(?:未提供|未取得|未给出|缺失)',
 '推测或反推':rf'(?:依据|根据|基于|按照|使用|通过).{{0,28}}{INFERENCE}|(?:据此|由此).{{0,8}}{INFERENCE}|HEX.{{0,20}}(?:无法确认|不足以证明|不能证明|不能还原)',
 '缺件后推测':rf'{GAP}.{{0,12}}{MATERIAL}.{{0,35}}{INFERENCE}',
 '作者编写过程':r'补齐(?:源码|源代码)|白盒需取得(?:源码|源代码)|根据现有产品功能建立|现有设计依据|保留模板结构|不据模板|不沿用其他产品|不得沿用其他产品|不移用.{0,12}允差|不预填.{0,12}合格|当前有证据的发布版本|不将互锁当作已实现|不能认定存在两级加密|不等同源码|不能等同源码|经验库默认|本轮仅(?:取得|完成文档)|IFU-derived',
}
REGEX={name:re.compile(value,re.I) for name,value in PATTERNS.items()}
RX=re.compile('|'.join(PATTERNS.values()),re.I)
PART=re.compile(r'word/(?:document|header\d*|footer\d*|comments\d*|footnotes|endnotes)\.xml$|(?:word|drawing)/.+\.xml$')
PARAS='//*[local-name()="p" and (namespace-uri()="http://schemas.openxmlformats.org/wordprocessingml/2006/main" or namespace-uri()="http://schemas.openxmlformats.org/drawingml/2006/main")]'
def check(folder):
    files=sorted(Path(folder).glob('RD-*.docx'));errors=[]
    if not files:return ['没有匹配的PEMS文档']
    for path in files:
        with zipfile.ZipFile(path) as package:
            for part in package.namelist():
                if not PART.fullmatch(part):continue
                root=etree.fromstring(package.read(part))
                for i,p in enumerate(root.xpath(PARAS),1):
                    text=''.join(p.xpath('.//*[local-name()="t"]/text()'))
                    for rule,pattern in REGEX.items():
                        if pattern.search(text):
                            errors.append({'file':path.name,'part':part,'paragraph':i,'rule':rule,'text':text})
    return errors
def main():
    ap=argparse.ArgumentParser();ap.add_argument('folder');ap.add_argument('--report');a=ap.parse_args()
    errors=check(a.folder)
    result={'pass':not errors,'files':len(list(Path(a.folder).glob('RD-*.docx'))),'errors':errors,
            'limit':'文本门禁仅检查成文措辞。图内字、连线及关键声明证据须单独复核。'}
    if a.report:Path(a.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
