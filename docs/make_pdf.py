#!/usr/bin/env python3
"""開發歷程.md -> 開發歷程.pdf（mermaid 圖在 PDF 中以 HTML 流程圖取代）"""
import re, asyncio, pathlib, markdown
from playwright.async_api import async_playwright
D = pathlib.Path(__file__).parent
md = (D/'開發歷程.md').read_text(encoding='utf-8')
DIAGRAM = '''<div class="arch">
<div class="row"><div class="box src">官方簡章／學習指引／抵免說明 PDF</div><div class="ar">→</div><div class="box">summary.md<br><small>評鑑項目樹</small></div><div class="ar">→</div><div class="box">study/src<br><small>講義 md／題目 txt／glossary.json</small></div></div>
<div class="lane"><b>網頁與講義</b>study/src →（build.py＋template.html）→ index.html 單檔離線 App；→（make_pdf.py）→ 講義.pdf</div>
<div class="lane"><b>有聲教材</b>summary.md → audio/scripts_v2 講稿 →（語音合成＋停頓處理）→ audio/v2/*.mp3</div>
<div class="lane"><b>部署</b>index.html＋講義.pdf＋mp3 → GitHub Pages 公開網站</div>
<div class="lane"><b>雲端同步</b>網站 App ⇄（進度合併 POST）⇄ Google Apps Script ⇄ Google 試算表 ipas_aiot_sync（Nelson 的雲端硬碟）</div>
<div class="lane"><b>課程影片</b>mp3 →（faster-whisper 對齊，video/align.py）→ 字幕與時間碼；講義 → slides.html；兩者 →（video/build.py＋HyperFrames）→ d02.mp4</div>
</div>'''
md = re.sub(r'```mermaid\n.*?```', 'MERMAIDPLACEHOLDER', md, flags=re.S)
body = markdown.markdown(md, extensions=['tables', 'fenced_code', 'sane_lists'])
body = body.replace('<p>MERMAIDPLACEHOLDER</p>', DIAGRAM)
font = (D.parent/'video/shared/fonts/NotoSansTC.ttf').as_uri()
html = f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><style>
@font-face{{font-family:NTC;src:url("{font}")}}
body{{font-family:"Noto Sans CJK TC","Noto Sans TC",sans-serif;font-size:10.5pt;line-height:1.7;color:#1f2937}}
h1{{font-size:21pt;color:#0f3d75;border-bottom:3px solid #0f3d75;padding-bottom:6px;margin-top:0}}
h2{{font-size:15pt;color:#0f3d75;border-left:6px solid #2563eb;padding-left:10px;margin-top:22px;page-break-after:avoid}}
h3{{font-size:12pt;color:#1e40af;margin-top:16px;page-break-after:avoid}}
blockquote{{background:#eff6ff;border-left:4px solid #93c5fd;margin:8px 0;padding:6px 12px;color:#334155}}
blockquote p{{margin:2px 0}}
table{{border-collapse:collapse;width:100%;margin:8px 0;font-size:9.5pt;page-break-inside:auto}}
tr{{page-break-inside:avoid}}
th{{background:#dbeafe;color:#0f3d75}} th,td{{border:1px solid #cbd5e1;padding:4px 7px;vertical-align:top}}
tr:nth-child(even) td{{background:#f8fafc}}
code{{background:#f1f5f9;padding:0 3px;border-radius:3px;font-size:9pt}}
hr{{border:0;border-top:1px solid #e2e8f0;margin:16px 0}}
li{{margin:2px 0}} td:first-child{{min-width:4.5em}}
.arch{{border:1px solid #cbd5e1;border-radius:8px;padding:10px;background:#f8fafc;page-break-inside:avoid}}
.row{{display:flex;align-items:center;gap:6px;margin-bottom:8px}}
.box{{flex:1;background:#fff;border:1.5px solid #2563eb;border-radius:6px;padding:6px;text-align:center;font-size:9.5pt}}
.box.src{{border-color:#16a34a}} .ar{{color:#2563eb;font-weight:bold}}
.lane{{background:#fff;border:1px solid #cbd5e1;border-radius:6px;padding:5px 8px;margin:5px 0;font-size:9.5pt}}
.lane b{{display:inline-block;min-width:5.5em;color:#0f3d75}}
</style></head><body>{body}</body></html>'''
(D/'_print.html').write_text(html, encoding='utf-8')
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg = await b.new_page()
        await pg.goto((D/'_print.html').as_uri()); await pg.wait_for_timeout(800)
        await pg.pdf(path=str(D/'開發歷程.pdf'), format='A4', print_background=True, display_header_footer=True,
            header_template='<div></div>',
            footer_template='<div style="width:100%;font-size:8px;color:#666;text-align:center">iPAS AIoT 學習平台 開發歷程　—　<span class="pageNumber"></span> / <span class="totalPages"></span></div>',
            margin={'top':'16mm','bottom':'18mm','left':'16mm','right':'16mm'})
        await b.close()
asyncio.run(main())
(D/'_print.html').unlink()
