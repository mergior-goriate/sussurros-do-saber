const {test,expect}=require('@playwright/test');
const {execFileSync}=require('node:child_process');
for(const width of [320,1440]){
  test(`drop cap toggles, persists and renders publicly at ${width}px`,async({page})=>{
    const cookie=execFileSync('python',['tests/browser/staff_fixture.py'],{encoding:'utf8'}).trim();
    const data=JSON.parse(execFileSync('python',['tests/browser/dropcap_fixture.py'],{encoding:'utf8'}));
    await page.context().addCookies([{name:'session',value:cookie,url:'http://127.0.0.1:5000',httpOnly:true,sameSite:'Lax'}]);
    await page.setViewportSize({width,height:1000});
    const path='/admin/artigos/'+data.article_id+'/editar';
    await page.goto(path);
    const editor=page.locator('#bodyEditor'), button=page.getByRole('button',{name:'Capitular',exact:true});
    const words=await page.locator('#editorWordCount').textContent();
    await editor.fill('[drop_cap] '+data.body);
    await editor.evaluate(el=>{el.focus();el.setSelectionRange(0,0);});
    await expect(button).toHaveAttribute('aria-pressed','true');
    await expect(page.locator('#editorWordCount')).toHaveText(words);
    await expect(page.locator('#markdownPreview .article-dropcap')).toHaveCount(1);
    await button.click();
    await expect(editor).toHaveValue(data.body);
    await button.click();
    await expect(button).toHaveAttribute('aria-pressed','true');
    await expect(editor).toHaveValue('[capitular] '+data.body);
    await expect(page.locator('#editorWordCount')).toHaveText(words);
    const preview=page.locator('#markdownPreview .article-dropcap');
    await expect(preview).toHaveCount(1);
    await expect(preview.locator('strong')).toHaveText('Texto em destaque');
    await expect(preview.locator('a')).toHaveAttribute('href','https://example.org');
    expect(await preview.evaluate(el=>parseFloat(getComputedStyle(el,'::first-letter').fontSize)/parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThan(2);
    await button.click();
    await expect(editor).toHaveValue(data.body);
    await expect(page.locator('#markdownPreview .article-dropcap')).toHaveCount(0);
    await button.click();
    await page.getByRole('button',{name:'Guardar artigo',exact:true}).click();
    await expect(page).toHaveURL(/\/admin\/artigos$/);
    await page.goto(path);
    await expect(editor).toHaveValue('[capitular] '+data.body);
    await expect(preview).toHaveCount(1);
    await page.getByRole('button',{name:'Alternar tema do painel',exact:true}).click();
    await page.screenshot({path:`/tmp/dropcap-previews/editor-dark-${width}.png`,fullPage:true,animations:'disabled'});
    await page.goto('/artigo/'+data.slug);
    const paragraph=page.locator('.article-markdown > p.article-dropcap');
    await expect(paragraph).toHaveCount(1);
    await expect(paragraph).toContainText('À medida que observamos');
    await expect(paragraph).not.toContainText('[capitular]');
    await expect(page.locator('.article-markdown > p:not(.article-dropcap)')).toContainText('Este segundo parágrafo');
    expect(await paragraph.evaluate(el=>getComputedStyle(el,'::first-letter').float)).toBe('left');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({path:`/tmp/dropcap-previews/public-light-${width}.png`,fullPage:true,animations:'disabled'});
    await page.locator('#themeToggle').click();
    await page.screenshot({path:`/tmp/dropcap-previews/public-dark-${width}.png`,fullPage:true,animations:'disabled'});
    await page.goto('/en/artigo/'+data.slug);
    const english=page.locator('.article-markdown > p.article-dropcap');
    await expect(english).toHaveText('An opening paragraph with emphasis.');
    await expect(english.locator('strong')).toHaveText('emphasis');
    expect(await english.evaluate(el=>getComputedStyle(el,'::first-letter').float)).toBe('left');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  });
}

for (const [name,path,field,button] of [
  ['news','/admin/noticias/nova','#news-body','[data-news-md="dropcap"]'],
  ['journal','/admin/revistas/nova','#journal-content-md','[data-md="dropcap"]']
]) {
  test(`shared drop cap grammar also works in the ${name} editor`,async({page})=>{
    const cookie=execFileSync('python',['tests/browser/staff_fixture.py'],{encoding:'utf8'}).trim();
    await page.context().addCookies([{name:'session',value:cookie,url:'http://127.0.0.1:5000',httpOnly:true,sameSite:'Lax'}]);
    await page.goto(path);
    const editor=page.locator(field),toggle=page.locator(button);
    for(const alias of ['[drop_cap]','[DROP-CAP]','[letra capitular]']){
      await editor.fill(alias+' A primeira frase.');
      await editor.evaluate(el=>{el.focus();el.setSelectionRange(0,0);});
      await toggle.click();
      await expect(editor).toHaveValue('A primeira frase.');
      await editor.evaluate(el=>{el.focus();el.setSelectionRange(0,0);});
      await toggle.click();
      await expect(editor).toHaveValue('[capitular] A primeira frase.');
    }
  });
}
