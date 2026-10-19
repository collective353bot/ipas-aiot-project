import json, asyncio
from playwright.async_api import async_playwright
URL='file:///workspace/ipas_aiot/study/index.html'
SS='/workspace/ipas_aiot/study/screenshots/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)
        pg=await ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m: m.type=='error' and errs.append(m.text))
        pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SS+'01_overview_mobile.png')
        await pg.goto(URL+'#/day/1/learn'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=SS+'02_day1_learn.png')
        await pg.goto(URL+'#/day/1/quiz'); await pg.wait_for_timeout(200)
        data=await pg.evaluate('DATA.days[0].questions.map(q=>q.ans)')
        # Q1 correct, Q2 wrong
        await pg.click(f'#q_d1q1 .opt[data-k="{data[0]}"]')
        await pg.click(f'#q_d1q2 .opt[data-k="{(data[1]+1)%4}"]')
        await pg.check('#donecb'); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelector('#q_d1q1').scrollIntoView()")
        await pg.screenshot(path=SS+'03_day1_quiz_feedback.png')
        st=json.loads(await pg.evaluate("localStorage.getItem('ipas_aiot_v1')"))
        print('after quiz:', {k:(len(v) if isinstance(v,dict) else v) for k,v in st.items()}, st['answers'])
        await pg.reload(); await pg.wait_for_timeout(200)
        print('persist feedback count:', await pg.locator('.fb').count(), 'done checked:', await pg.is_checked('#donecb'))
        await pg.goto(URL+'#/wrong'); await pg.wait_for_timeout(200)
        print('wrong cards:', await pg.locator('.q').count())
        await pg.click(f'.q .opt[data-k="{data[1]}"]'); await pg.wait_for_timeout(100)
        st=json.loads(await pg.evaluate("localStorage.getItem('ipas_aiot_v1')"))
        print('wrong after redo:', st['wrong'])
        # mock
        await pg.goto(URL+'#/day/6/mock'); await pg.wait_for_timeout(200)
        await pg.click('#mstart'); await pg.wait_for_timeout(300)
        ans=await pg.evaluate('DATA.days[5].questions.map(q=>q.ans)')
        qs=pg.locator('.q')
        for i in range(30):
            k=ans[i] if i%4 else (ans[i]+1)%4
            await qs.nth(i).locator('.opt').nth(k).click()
        await pg.evaluate('window.scrollTo(0,0)')
        await pg.screenshot(path=SS+'04_mock_running.png')
        await pg.reload(); await pg.wait_for_timeout(300)
        print('mock sel persisted:', await pg.locator('.opt.sel').count(), 'timer:', await pg.text_content('#tm'))
        await pg.click('#msub'); await pg.wait_for_timeout(400)
        print('score text:', (await pg.text_content('.score')).strip())
        await pg.screenshot(path=SS+'05_mock_result.png')
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SS+'06_overview_after.png', full_page=True)
        print('nav:', await pg.text_content('nav'))
        # desktop overview
        pg2=await (await b.new_context(viewport={'width':1280,'height':900})).new_page()
        await pg2.goto(URL+'#/map'); await pg2.wait_for_timeout(300)
        await pg2.screenshot(path=SS+'07_map_desktop.png', full_page=True)
        for r in ['#/cheat','#/settings','#/day/12/mock','#/day/13/quiz','#/day/9/learn']:
            await pg2.goto(URL+r); await pg2.wait_for_timeout(150)
        await pg2.goto(URL+'#/day/10/learn'); await pg2.wait_for_timeout(200)
        await pg2.screenshot(path=SS+'08_day10_learn_desktop.png')
        # horizontal overflow check on mobile
        for r in ['#/','#/day/3/learn','#/day/10/learn','#/day/11/learn','#/cheat','#/map']:
            await pg.goto(URL+r); await pg.wait_for_timeout(150)
            ov=await pg.evaluate('document.documentElement.scrollWidth')
            print(r,'scrollWidth',ov)
        print('errors:', errs)
        await b.close()
asyncio.run(main())
