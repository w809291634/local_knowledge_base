# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0, '.')
from docx import Document
import para_ops as P

OUT = r'D:\current_work\我的工作资料汇总\注册文档\07-03GSR2607002（元良）半导体激光治疗仪\qoder_PEMS-嵌入式'
CLS = r'D:\current_work\我的工作资料汇总\注册文档\07-03GSR2607002（元良）半导体激光治疗仪\qoder_work'
tot_d = tot_f = 0
for fn in sorted(os.listdir(OUT)):
    if not fn.endswith('.docx'):
        continue
    k = fn.split()[0]
    doc = Document(os.path.join(OUT, fn))
    try:
        cls = json.load(open(os.path.join(CLS, 'para_class_%s.json' % k), encoding='utf-8'))
    except Exception:
        cls = {}
    co = lambda p: cls.get(P.nws(p.text)[:60], 'base')
    allow = [tuple(x) for x in json.load(open(os.path.join(CLS, 'qoder_config.json'), encoding='utf-8'))['key'][k].get('dup_allow', [])]
    d = P.find_duplicate_paragraphs(doc, allow)
    longs = P.body_paragraphs(doc)
    f = P.para_format_issues(doc, longs, co)
    tot_d += len(d); tot_f += len(f)
    print('%-34s 重复=%d 版式不一致=%d %s' % (fn[:34], len(d), len(f), [x[0] for x in d][:3]))
print('TOTAL dup=%d fmt=%d' % (tot_d, tot_f))
