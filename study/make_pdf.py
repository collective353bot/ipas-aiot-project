import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page()
        await pg.goto('file:///workspace/ipas_aiot/study/print.html'); await pg.wait_for_timeout(800)
        await pg.pdf(path='/workspace/ipas_aiot/study/講義.pdf', format='A4', print_background=True, display_header_footer=True,
            header_template='<div></div>',
            footer_template='<div style="width:100%;font-size:8px;color:#666;text-align:center;font-family:sans-serif">iPAS AIoT 應用工程師（初級）13 天講義　—　<span class="pageNumber"></span> / <span class="totalPages"></span></div>',
            margin={'top':'16mm','bottom':'18mm','left':'14mm','right':'14mm'})
        await b.close()
asyncio.run(main())
