"""Paragraph-first splitting shared by every engine; never silently drops text."""
import re

def split_narration(text,limit=100):
    text=text.strip();limit=int(limit)
    if not text:raise ValueError('请填写完整配音文案。')
    if len(text)>12000:raise ValueError('文案最多 12000 字符，更长请拆成多个项目。')
    if not 40<=limit<=160:raise ValueError('分段长度应在 40～160 字符之间。')
    result=[]
    for paragraph in text.splitlines():
        remaining=paragraph.strip()
        while len(remaining)>limit:
            # Keep newlines as the primary boundary. Prefer sentences, then words.
            boundaries=[m.end() for m in re.finditer(r'[。！？；!?;]|[.](?=\s)',remaining[:limit+1]) if m.end()<=limit]
            cut=boundaries[-1] if boundaries and boundaries[-1]>=limit//3 else 0
            if not cut:
                candidates=[m.end() for m in re.finditer(r'\s+|[，,、：:]',remaining[:limit+1]) if m.end()<=limit]
                cut=candidates[-1] if candidates and candidates[-1]>=limit//3 else limit
                # A long English word or identifier must not be cut mid-word.
                if cut==limit and remaining[cut-1:cut+1].isascii() and remaining[cut-1:cut+1].isalpha():
                    boundary=re.search(r'\s|[^\x00-\x7f]',remaining[limit:])
                    if boundary and limit+boundary.start()<=200:cut=limit+boundary.start()
                    else:raise ValueError('遇到超过安全长度的英文单词或网址，请缩短该行。')
            result.append(remaining[:cut].strip());remaining=remaining[cut:].strip()
        if remaining:result.append(remaining)
    if re.sub(r'\s','',text)!=re.sub(r'\s','',''.join(result)):raise ValueError('分段校验失败，未保存项目。')
    return result
