import asyncio, pathlib
from playwright.async_api import async_playwright
H=pathlib.Path(__file__).parent
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page(viewport={'width':1920,'height':1080})
        await pg.goto((H/'proto.html').as_uri()); await pg.wait_for_timeout(1200)
        for sid in ['a3','a4','a13','a29','b13']:
            await pg.locator('#'+sid).screenshot(path=str(H/f'{sid}.png'))
        await b.close()
asyncio.run(main())
