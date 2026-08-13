from playwright.sync_api import sync_playwright
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
base=Path(__file__).resolve().parent
html=(base/'ege-russkiy-demoversiya-PREVIEW.html').read_text('utf-8')
out=base/'visual-audit-screens'; out.mkdir(exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':1100})
    pg.set_content(html,wait_until='domcontentloaded')
    pg.click('#edemo-start')
    for n in range(1,28):
        pg.locator('#edemo-nav .edemo-nav-btn').nth(n-1).click()
        loc=pg.locator('#edemo-task-stage')
        loc.screenshot(path=str(out/f'task-{n:02d}.png'))
    b.close()
# contact sheets, scaled widths 380
for batch in range(3):
    nums=range(batch*9+1,min(batch*9+10,28))
    thumbs=[]
    for n in nums:
        im=Image.open(out/f'task-{n:02d}.png').convert('RGB')
        w=380; h=max(1,round(im.height*w/im.width)); im=im.resize((w,h))
        canvas=Image.new('RGB',(w,h+28),'white'); canvas.paste(im,(0,28))
        ImageDraw.Draw(canvas).text((8,6),f'TASK {n}',fill='black')
        thumbs.append(canvas)
    W=380*3; rows=(len(thumbs)+2)//3; rowheights=[]
    for r in range(rows): rowheights.append(max(x.height for x in thumbs[r*3:(r+1)*3]))
    sheet=Image.new('RGB',(W,sum(rowheights)),'white'); y=0
    for r in range(rows):
        for c,x in enumerate(thumbs[r*3:(r+1)*3]): sheet.paste(x,(c*380,y))
        y+=rowheights[r]
    sheet.save(out/f'sheet-{batch+1}.jpg',quality=85)
print(out)
