import asyncio, pathlib
from playwright.async_api import async_playwright
H=pathlib.Path(__file__).parent
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page(viewport={'width':1920,'height':1080})
        await pg.goto((H/'proto2.html').as_uri()); await pg.wait_for_timeout(1200)
        for sid in ['w_cover','w_a13','w_b13','l_cover','l_a13','l_b13']:
            await pg.locator('#'+sid).screenshot(path=str(H/f'{sid}.png'))
        await b.close()
asyncio.run(main())
