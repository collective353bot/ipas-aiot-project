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
        # ---------- glossary tooltips / glossary page / checkpoints ----------
        ctxd=await b.new_context(viewport={'width':1280,'height':900})
        pd=await ctxd.new_page(); pd.on('pageerror',lambda e:errs.append(str(e))); pd.on('console',lambda m: m.type=='error' and errs.append(m.text))
        await pd.goto(URL+'#/day/8/learn'); await pd.wait_for_timeout(300)
        g=pd.locator('.lec .gl').nth(3); await g.scroll_into_view_if_needed(); await pd.mouse.wheel(0,-150); await pd.wait_for_timeout(100)
        await g.hover(); await pd.wait_for_timeout(250)
        vis=await pd.evaluate("(()=>{const p=document.getElementById('glpop');if(!p)return null;const r=p.getBoundingClientRect();return {disp:getComputedStyle(p).display,l:r.left,r:r.right,t:r.top,b:r.bottom,txt:p.innerText.slice(0,40)}})()")
        print('desktop hover tooltip:', vis)
        assert vis and vis['disp']=='block'
        await pd.screenshot(path=SS+'tooltip_desktop.png')
        await pd.mouse.move(5,600); await pd.wait_for_timeout(400)
        print('desktop tooltip hidden after mouseout:', await pd.evaluate("getComputedStyle(document.getElementById('glpop')).display"))
        # glossary page
        await pd.goto(URL+'#/glossary'); await pd.wait_for_timeout(300)
        tot=await pd.locator('.gitem:visible').count()
        await pd.fill('#gq','SCADA'); await pd.wait_for_timeout(150)
        hits=await pd.locator('.gitem:visible').count()
        print('glossary items:', tot, 'search SCADA hits:', hits, await pd.text_content('#gcnt'))
        assert 0<hits<tot
        await pd.fill('#gq','致動器'); await pd.wait_for_timeout(150)
        print('search 致動器 hits:', await pd.locator('.gitem:visible').count())
        await pd.screenshot(path=SS+'glossary_page.png')
        await pd.goto(URL+'#/glossary?q=MCU'); await pd.wait_for_timeout(300)
        print('deep link q=MCU hits:', await pd.locator('.gitem:visible').count())
        # checkpoint
        before=await pd.evaluate("localStorage.getItem('ipas_aiot_v1')")
        await pd.goto(URL+'#/day/1/learn'); await pd.wait_for_timeout(300)
        cp=pd.locator('.cp').first; await cp.scroll_into_view_if_needed()
        ans=int(await cp.get_attribute('data-ans'))
        await cp.locator('.cpo').nth((ans+1)%4).click(); await pd.wait_for_timeout(150)
        fb=await cp.locator('.cpfb').is_visible(); txt=await cp.locator('.cpr').text_content()
        print('checkpoint feedback visible:', fb, txt, 'right marked:', await cp.locator('.cpo.right').count())
        assert fb
        await cp.evaluate("e=>e.scrollIntoView({block:'center'})"); await pd.wait_for_timeout(100)
        await pd.screenshot(path=SS+'checkpoint.png')
        after=await pd.evaluate("localStorage.getItem('ipas_aiot_v1')")
        print('progress unchanged by checkpoint:', before==after)
        print('checkpoint counts:', await pd.evaluate("DATA.days.map(d=>d.checks.length)"))
        await pd.click('#gdict summary'); await pd.wait_for_timeout(100)
        print('day dictionary open:', await pd.evaluate("document.getElementById('gdict').open"), 'items:', await pd.locator('#gdict .gitem').count())
        # mobile tap
        ctxm=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,has_touch=True,is_mobile=True)
        pm=await ctxm.new_page(); pm.on('pageerror',lambda e:errs.append(str(e))); pm.on('console',lambda m: m.type=='error' and errs.append(m.text))
        await pm.goto(URL+'#/day/8/learn'); await pm.wait_for_timeout(300)
        worst=None
        n=await pm.locator('.lec .gl:visible').count()
        for i in [0,5,n//2,n-1]:
            g=pm.locator('.lec .gl:visible').nth(i); await g.scroll_into_view_if_needed(); await pm.wait_for_timeout(80)
            await g.tap(); await pm.wait_for_timeout(150)
            r=await pm.evaluate("(()=>{const p=document.getElementById('glpop');const r=p.getBoundingClientRect();return {disp:getComputedStyle(p).display,l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom)}})()")
            print('mobile tap tooltip', i, r); assert r['disp']=='block' and r['l']>=0 and r['r']<=390 and r['t']>=0 and r['b']<=844
            if i==5: await pm.screenshot(path=SS+'tooltip_mobile.png')
        await pm.tap('h1'); await pm.wait_for_timeout(150)
        print('mobile tap elsewhere closes:', await pm.evaluate("getComputedStyle(document.getElementById('glpop')).display"))
        await pm.goto(URL+'#/glossary'); await pm.wait_for_timeout(300)
        print('#/glossary mobile scrollWidth', await pm.evaluate('document.documentElement.scrollWidth'))
        await pm.goto(URL+'#/audio'); await pm.wait_for_timeout(200)
        print('audio srcs:', await pm.evaluate("[...document.querySelectorAll('audio')].slice(0,2).map(a=>a.getAttribute('src'))"))
        print('errors:', errs)
        await b.close()
asyncio.run(main())
