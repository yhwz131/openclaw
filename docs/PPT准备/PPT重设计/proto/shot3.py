import asyncio, pathlib
from playwright.async_api import async_playwright
H=pathlib.Path(__file__).parent
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page(viewport={'width':1920,'height':1080})
        await pg.goto((H/'proto3.html').as_uri()); await pg.wait_for_timeout(1200)
        for sid in ['m_cover','m_a13','m_b13']:
            await pg.locator('#'+sid).screenshot(path=str(H/f'{sid}_v2.png'))
        await b.close()
asyncio.run(main())
