import asyncio, pathlib
from playwright.async_api import async_playwright
H=pathlib.Path(__file__).parent
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page(viewport={'width':1920,'height':1080})
        await pg.goto((H/'proto7.html').as_uri()); await pg.wait_for_timeout(1200)
        for sid in ['e_a13','e_a17','e_a26','e_b13','e_b17','e_b26']:
            await pg.locator('#'+sid).screenshot(path=str(H/f'{sid}_v4.png'))
        await b.close()
asyncio.run(main())
