import asyncio, pathlib
from playwright.async_api import async_playwright
H=pathlib.Path(__file__).parent
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page(viewport={'width':1920,'height':1080})
        await pg.goto((H/'proto6.html').as_uri()); await pg.wait_for_timeout(1200)
        for sid in ['d_a17','d_b17','d_a26','d_b26']:
            await pg.locator('#'+sid).screenshot(path=str(H/f'{sid}_v3.png'))
        await b.close()
asyncio.run(main())
