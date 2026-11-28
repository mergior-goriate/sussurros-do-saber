(() => {
  const editor = document.querySelector('#bodyEditor');
  const preview = document.querySelector('#markdownPreview');
  if (!editor || !preview) return;

  const dropcap = window.editorialDropcap;
  const escape = (text) => text.replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const videoPreview = (title, rawUrl) => {
    try {
      const url = new URL(rawUrl.replace(/&amp;/g,'&'));
      const host = url.hostname.toLowerCase().replace(/^www\./,'');
      let embed = '';
      if (['youtube.com','m.youtube.com','youtube-nocookie.com'].includes(host)) {
        const id = url.pathname.includes('/embed/') ? url.pathname.split('/embed/')[1].split('/')[0] : url.searchParams.get('v');
        if (/^[A-Za-z0-9_-]{6,20}$/.test(id||'')) embed = `https://www.youtube-nocookie.com/embed/${id}`;
      } else if (host === 'youtu.be') {
        const id=url.pathname.slice(1).split('/')[0]; if (/^[A-Za-z0-9_-]{6,20}$/.test(id)) embed=`https://www.youtube-nocookie.com/embed/${id}`;
      } else if (['vimeo.com','player.vimeo.com'].includes(host)) {
        const match=url.pathname.match(/(?:video\/)?(\d{5,12})/); if(match)embed=`https://player.vimeo.com/video/${match[1]}`;
      }
      if(embed)return `<figure class="preview-video"><div><iframe src="${embed}" title="${title}" loading="lazy"></iframe></div><figcaption>${title}</figcaption></figure>`;
      if (/\.(mp4|webm|ogg)$/i.test(url.pathname)) return `<figure class="preview-video"><video src="${escape(rawUrl)}" controls preload="metadata"></video><figcaption>${title}</figcaption></figure>`;
    } catch {}
    return `<p><a href="${escape(rawUrl)}">Vídeo: ${title}</a></p>`;
  };
  let estimatedReadingMinutes = 1;
  const updateEditorStatistics = () => {
    const words = dropcap.withoutMarkers(editor.value).match(/[\p{L}\p{N}]+(?:[’'-][\p{L}\p{N}]+)*/gu) || [];
    estimatedReadingMinutes = Math.max(1, Math.min(120, Math.ceil(words.length / 200)));
    const count = document.querySelector('#editorWordCount');
    const reading = document.querySelector('#editorReadingTime');
    if (count) count.textContent = `${words.length} palavras`;
    if (reading) reading.textContent = `${estimatedReadingMinutes} min de leitura estimada`;
  };
  const render = () => {
    updateEditorStatistics();
    // The authenticated server preview uses the public Markdown renderer.
    editor.dispatchEvent(new Event('editor:rendered'));
  };

  const dropcapButton = document.querySelector('#toggleDropcap');
  const dropcapStatus = document.querySelector('#dropcapStatus');
  const currentParagraph = () => {
    const value = editor.value, cursor = editor.selectionStart;
    const breaks = /\n[ \t]*\n/g;
    let start = 0, match;
    while ((match = breaks.exec(value)) && match.index + match[0].length <= cursor) start = match.index + match[0].length;
    const rest = value.slice(start), end = rest.search(/\n[ \t]*\n/);
    return {start, text: end < 0 ? rest : rest.slice(0,end)};
  };
  const updateDropcapState = () => {
    if (dropcapButton) dropcapButton.setAttribute('aria-pressed', String(Boolean(dropcap.marker(currentParagraph().text))));
  };
  dropcapButton?.addEventListener('click', () => {
    const {start,text} = currentParagraph();
    if (/^\s*(?:#{1,6}\s|>|[-*+]\s|\d+[.)]\s|\x60{3}|~{3}|\||!\[|\[(?:destaque|chart|video|portrait):)/.test(text)) {
      dropcapStatus.textContent = 'Coloque o cursor num parágrafo de texto para aplicar a capitular.';
      return;
    }
    const marker = dropcap.marker(text);
    const cursor = editor.selectionStart;
    editor.setRangeText(marker ? '' : dropcap.canonical, start, marker ? start+marker.length : start, 'preserve');
    const next = Math.max(start,cursor+(marker ? -marker.length : dropcap.canonical.length));
    editor.setSelectionRange(next,next);
    dropcapStatus.textContent = marker ? 'Capitular removida deste parágrafo.' : 'Capitular aplicada a este parágrafo.';
    editor.focus(); render(); updateDropcapState();
  });
  for (const event of ['click','keyup','select','input','editor:rendered']) editor.addEventListener(event,updateDropcapState);
  updateDropcapState();

  document.querySelectorAll('.editor-toolbar button[data-before]').forEach((button) => button.addEventListener('click', () => {
    const start=editor.selectionStart,end=editor.selectionEnd,before=button.dataset.before||'',after=button.dataset.after||'';
    editor.setRangeText(before+editor.value.slice(start,end)+after,start,end,'end');
    editor.focus();
    render();
  }));

  document.querySelectorAll('.editor-toolbar button[data-heading]').forEach(button => {
    button.addEventListener('click', () => {
      const start = editor.selectionStart === 0 ? 0 : editor.value.lastIndexOf('\n', editor.selectionStart - 1) + 1;
      const selectedEnd = editor.selectionEnd > editor.selectionStart && editor.value[editor.selectionEnd - 1] === '\n' ? editor.selectionEnd - 1 : editor.selectionEnd;
      const lineEnd = editor.value.indexOf('\n', selectedEnd);
      const end = lineEnd < 0 ? editor.value.length : lineEnd;
      const selected = editor.value.slice(start, end);
      const prefix = '#'.repeat(Number(button.dataset.heading)) + ' ';
      editor.setRangeText(selected.split('\n').map(line => prefix + line.replace(/^#{1,6} +/, '')).join('\n'), start, end, 'end');
      editor.focus();
      editor.dispatchEvent(new Event('input', {bubbles: true}));
    });
  });

  const explainerPanel=document.querySelector('#explainerPanel');
  const openExplainer=document.querySelector('#openExplainer');
  const explainerTitle=document.querySelector('#explainerTitle');
  const explainerBody=document.querySelector('#explainerBody');
  const explainerStatus=document.querySelector('#explainerStatus');
  const explainerColor=document.querySelector('#explainerColor');
  const explainerCustomColor=document.querySelector('#explainerCustomColor');
  const explainerColorPreview=document.querySelector('#explainerColorPreview');
  const explainerForeground=color=>{
    const rgb=[1,3,5].map(i=>parseInt(color.slice(i,i+2),16)/255);
    const linear=rgb.map(c=>c<=0.04045?c/12.92:((c+0.055)/1.055)**2.4);
    const luminance=linear.reduce((sum,c,i)=>sum+c*[0.2126,0.7152,0.0722][i],0);
    return (luminance+0.05)/0.05>=1.05/(luminance+0.05)?'#000000':'#ffffff';
  };
  const updateExplainerPreview=()=>{
    if(!explainerColorPreview)return;
    const color=explainerColor.value.toLowerCase();
    if(explainerCustomColor.checked&&/^#[0-9a-f]{6}$/.test(color)){
      explainerColorPreview.style.setProperty('--explainer-bg',color);
      explainerColorPreview.style.setProperty('--explainer-fg',explainerForeground(color));
    }else{
      explainerColorPreview.style.removeProperty('--explainer-bg');
      explainerColorPreview.style.removeProperty('--explainer-fg');
    }
    document.querySelector('#explainerPreviewTitle').textContent=explainerTitle.value.trim()||'Caixa explicativa';
    document.querySelector('#explainerPreviewBody').textContent=explainerBody.value.trim()||'A sua explicação aparecerá com este fundo.';
  };
  explainerColor?.addEventListener('input',()=>{explainerCustomColor.checked=true;updateExplainerPreview();});
  explainerCustomColor?.addEventListener('change',updateExplainerPreview);
  for(const field of [explainerTitle,explainerBody])field?.addEventListener('input',updateExplainerPreview);
  document.querySelector('#resetExplainerColor')?.addEventListener('click',()=>{
    explainerCustomColor.checked=false;explainerColor.value='#ffead0';updateExplainerPreview();
  });
  let explainerStart=0,explainerEnd=0,explainerSource='',editingExplainer=false,legacyExplainer=false;
  const closeExplainer=()=>{
    explainerPanel.hidden=true;openExplainer.setAttribute('aria-expanded','false');openExplainer.focus();
  };
  openExplainer?.addEventListener('click',()=>{
    if(!explainerPanel.hidden){closeExplainer();return}
    explainerSource=editor.value;explainerStart=editor.selectionStart;explainerEnd=editor.selectionEnd;
    editingExplainer=false;legacyExplainer=false;explainerTitle.value='';
    explainerBody.value=editor.value.slice(explainerStart,explainerEnd);
    if(explainerCustomColor){explainerCustomColor.checked=false;explainerColor.value='#ffead0';}
    const boxes=/^\[caixa:[ \t]*([^\]\n|]*)(?:\|(right|full))?(?:\|([^\]\n]*))?\][ \t]*\n([\s\S]*?)^\[\/caixa\][ \t]*(?=\n|$)/gm;
    let box;
    while((box=boxes.exec(editor.value))){
      if(explainerStart>=box.index&&explainerEnd<=box.index+box[0].length){
        editingExplainer=true;explainerStart=box.index;explainerEnd=box.index+box[0].length;
        explainerTitle.value=box[1].trim();explainerBody.value=box[4].trim();
        document.querySelector('#explainerLayout').value=box[2]||'right';
        if(explainerCustomColor&&/^#[0-9a-f]{6}$/i.test((box[3]||'').trim())){
          explainerCustomColor.checked=true;explainerColor.value=box[3].trim().toLowerCase();
        }
        break;
      }
    }
    if(!editingExplainer){
      const legacyBoxes=/\\n\\n(\[caixa:[^\]\r\n]*\])\\n([\s\S]*?)\\n\[\/caixa\]\\n\\n/g;
      while((box=legacyBoxes.exec(editor.value))){
        if(explainerStart<box.index||explainerEnd>box.index+box[0].length)continue;
        const header=box[1].match(/^\[caixa:[ \t]*([^\]\n|]*)(?:\|(right|full))?(?:\|([^\]\n]*))?\]$/);
        if(!header)continue;
        editingExplainer=true;legacyExplainer=true;explainerStart=box.index;explainerEnd=box.index+box[0].length;
        explainerTitle.value=header[1].trim();explainerBody.value=box[2].trim();
        document.querySelector('#explainerLayout').value=header[2]||'right';
        if(explainerCustomColor&&/^#[0-9a-f]{6}$/i.test((header[3]||'').trim())){
          explainerCustomColor.checked=true;explainerColor.value=header[3].trim().toLowerCase();
        }
        break;
      }
    }
    document.querySelector('#insertExplainer').textContent=editingExplainer?'Actualizar caixa':'Inserir caixa';
    updateExplainerPreview();
    explainerStatus.textContent='';explainerPanel.hidden=false;
    openExplainer.setAttribute('aria-expanded','true');explainerTitle.focus();
  });
  document.querySelector('#closeExplainer')?.addEventListener('click',closeExplainer);
  explainerPanel?.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();closeExplainer()}});
  document.querySelector('#insertExplainer')?.addEventListener('click',()=>{
    if(editor.value!==explainerSource){explainerStatus.textContent='O texto mudou. Feche e volte a abrir a caixa na posição desejada.';return}
    const title=explainerTitle.value.trim().replace(/[\r\n\[\]|]+/g,' ');
    const body=explainerBody.value.trim();
    if(!body){explainerStatus.textContent='Escreva a explicação.';explainerBody.focus();return}
    if(/^\[\/?caixa[:\]]/m.test(body)){explainerStatus.textContent='Retire os marcadores de caixa do texto da explicação.';return}
    const layout=document.querySelector('#explainerLayout').value==='full'?'full':'right';
    const color=explainerCustomColor?.checked?explainerColor.value.toLowerCase():'';
    if(color&&!/^#[0-9a-f]{6}$/.test(color)){explainerStatus.textContent='Escolha uma cor de fundo válida.';return;}
    const space=editingExplainer&&!legacyExplainer?'':'\n\n';
    const markup=space+'[caixa: '+title+'|'+layout+(color?'|'+color:'')+']\n'+body+'\n[/caixa]'+space;
    if(editor.value.length-(explainerEnd-explainerStart)+markup.length>400000){explainerStatus.textContent='A caixa excede o limite de tamanho do artigo.';return}
    editor.setRangeText(markup,explainerStart,explainerEnd,'end');
    explainerTitle.value='';explainerBody.value='';closeExplainer();editor.focus();
    editor.dispatchEvent(new Event('input',{bubbles:true}));
  });

  const panel=document.querySelector('#inlineImagePanel');
  const openButton=document.querySelector('#openInlineImage');
  const closeButton=document.querySelector('#closeInlineImage');
  const insertButton=document.querySelector('#insertInlineImage');
  const inlineFile=document.querySelector('#inlineImageFile');
  const inlineUrl=document.querySelector('#inlineImageUrl');
  const inlineAlt=document.querySelector('#inlineImageAlt');
  const inlineCaption=document.querySelector('#inlineImageCaption');
  const inlineStatus=document.querySelector('#inlineImageStatus');
  let insertionPoint=0;

  const setPanel=(open)=>{
    panel.hidden=!open;
    openButton.setAttribute('aria-expanded',String(open));
    if(open){insertionPoint=editor.selectionStart;inlineAlt.focus()}else{openButton.focus()}
  };
  openButton?.addEventListener('click',()=>setPanel(panel.hidden));
  closeButton?.addEventListener('click',()=>setPanel(false));

  const cleanText=(value)=>value.trim().replace(/[\r\n\[\]]+/g,' ');
  const uploadImage=async(file)=>{
    const data=new FormData();
    data.append('csrf_token',document.querySelector('input[name="csrf_token"]').value);
    data.append('image',file);
    const response=await fetch('/admin/api/imagens',{method:'POST',body:data,headers:{'Accept':'application/json'}});
    const result=await response.json().catch(()=>({error:'Resposta inválida do servidor.'}));
    if(!response.ok||!result.ok)throw new Error(result.error||'Não foi possível carregar a imagem.');
    return result.url;
  };

  insertButton?.addEventListener('click',async()=>{
    const alt=cleanText(inlineAlt.value);
    const caption=cleanText(inlineCaption.value);
    const file=inlineFile.files[0];
    let url=inlineUrl.value.trim();
    if(!alt){inlineStatus.textContent='Escreva uma descrição acessível da imagem.';inlineAlt.focus();return}
    if(!file&&!url){inlineStatus.textContent='Seleccione um ficheiro ou informe o endereço da imagem.';return}
    if(url&&!/^https?:\/\//i.test(url)){inlineStatus.textContent='O endereço deve começar por https:// ou http://.';inlineUrl.focus();return}
    insertButton.disabled=true;
    inlineStatus.textContent=file?'A carregar imagem...':'A inserir imagem...';
    try{
      if(file)url=await uploadImage(file);
      const layout=document.querySelector('#inlineImageLayout').value;
      const credit=cleanText(document.querySelector('#inlineImageCredit').value);
      const safeUrl=url.replace(/\(/g,'%28').replace(/\)/g,'%29');
      const parts=[alt,caption,credit].map(text=>text.replace(/\|/g,' '));
      const markdown=layout==='portrait'
        ? '\n\n[portrait: '+parts.join('|')+']('+safeUrl+')\n\n'
        : '\n\n!['+alt+']('+safeUrl+')'+(caption?'\n*'+caption+'*':'')+(credit?'\n*Crédito: '+credit+'*':'')+'\n\n';
      editor.setRangeText(markdown,insertionPoint,insertionPoint,'end');
      render();
      inlineFile.value='';inlineUrl.value='';inlineAlt.value='';inlineCaption.value='';
      inlineStatus.textContent='Imagem inserida no artigo.';
      setPanel(false);
      editor.focus();
    }catch(error){inlineStatus.textContent=error.message}
    finally{insertButton.disabled=false}
  });

  const videoPanel=document.querySelector('#inlineVideoPanel');
  const openVideo=document.querySelector('#openInlineVideo');
  const closeVideo=document.querySelector('#closeInlineVideo');
  const insertVideo=document.querySelector('#insertInlineVideo');
  const videoUrl=document.querySelector('#inlineVideoUrl');
  const videoTitle=document.querySelector('#inlineVideoTitleInput');
  const videoStatus=document.querySelector('#inlineVideoStatus');
  let videoInsertionPoint=0;
  const setVideoPanel=(open)=>{
    videoPanel.hidden=!open;
    openVideo.setAttribute('aria-expanded',String(open));
    if(open){videoInsertionPoint=editor.selectionStart;videoUrl.focus()}else{openVideo.focus()}
  };
  openVideo?.addEventListener('click',()=>setVideoPanel(videoPanel.hidden));
  closeVideo?.addEventListener('click',()=>setVideoPanel(false));
  insertVideo?.addEventListener('click',async()=>{
    let url=videoUrl.value.trim();
    const title=cleanText(videoTitle.value),file=document.querySelector('#inlineVideoFile').files[0];
    if(file && (file.size > 50*1024*1024 || !/\.(mp4|webm|ogg)$/i.test(file.name))){videoStatus.textContent='Use MP4, WebM ou OGG com no máximo 50 MB.';return}
    if(file){
      if(!title){videoStatus.textContent='Escreva um título ou uma legenda para o vídeo.';return}
      insertVideo.disabled=true;videoStatus.textContent='A carregar vídeo...';
      try{
        const data=new FormData();
        data.append('csrf_token',document.querySelector('input[name="csrf_token"]').value);
        data.append('video',file);
        const response=await fetch('/admin/api/videos',{method:'POST',body:data,headers:{'Accept':'application/json'}});
        const result=await response.json().catch(()=>({error:'Não foi possível carregar o vídeo. Verifique o tamanho e tente novamente.'}));
        if(!response.ok||!result.ok)throw new Error(result.error||'Não foi possível carregar o vídeo.');
        url=result.url;videoUrl.value=url;document.querySelector('#inlineVideoFile').value='';
      }catch(error){videoStatus.textContent=error.message;return}
      finally{insertVideo.disabled=false}
    }
    if(!/^https?:\/\//i.test(url)){videoStatus.textContent='Informe um endereço válido iniciado por https://.';videoUrl.focus();return}
    if(!title){videoStatus.textContent='Escreva um título ou uma legenda para o vídeo.';videoTitle.focus();return}
    try{
      const parsed=new URL(url),host=parsed.hostname.toLowerCase().replace(/^www\./,'');
      const direct=/\.(mp4|webm|ogg)$/i.test(parsed.pathname);
      const supported=['youtube.com','m.youtube.com','youtube-nocookie.com','youtu.be','vimeo.com','player.vimeo.com'].includes(host)||direct;
      if(!supported){videoStatus.textContent='Use uma ligação do YouTube, Vimeo, MP4, WebM ou OGG.';return}
      editor.setRangeText(`\n\n[video: ${title}](${url})\n\n`,videoInsertionPoint,videoInsertionPoint,'end');
      render();videoUrl.value='';videoTitle.value='';videoStatus.textContent='Vídeo inserido no artigo.';setVideoPanel(false);editor.focus();
    }catch{videoStatus.textContent='O endereço do vídeo não é válido.'}
  });

  const tablePanel=document.querySelector('#tablePanel'),openTable=document.querySelector('#openTable'),closeTable=document.querySelector('#closeTable'),insertTable=document.querySelector('#insertTable'),tableColumns=document.querySelector('#tableColumns'),tableRows=document.querySelector('#tableRows'),tableStatus=document.querySelector('#tableStatus');
  let tableInsertionPoint=0;
  const setTablePanel=(open)=>{tablePanel.hidden=!open;openTable.setAttribute('aria-expanded',String(open));if(open){tableInsertionPoint=editor.selectionStart;tableColumns.focus()}else{openTable.focus()}};
  openTable?.addEventListener('click',()=>setTablePanel(tablePanel.hidden));
  closeTable?.addEventListener('click',()=>setTablePanel(false));
  insertTable?.addEventListener('click',()=>{
    const columns=Math.max(2,Math.min(8,Number(tableColumns.value)||3)),rows=Math.max(1,Math.min(20,Number(tableRows.value)||3));
    const header='| '+Array.from({length:columns},(_,index)=>`Coluna ${index+1}`).join(' | ')+' |';
    const separator='| '+Array(columns).fill('---').join(' | ')+' |';
    const body=Array.from({length:rows},()=>('| '+Array(columns).fill('Conteúdo').join(' | ')+' |')).join('\n');
    editor.setRangeText(`\n\n${header}\n${separator}\n${body}\n\n`,tableInsertionPoint,tableInsertionPoint,'end');
    render();tableStatus.textContent='Tabela inserida. Edite os títulos e conteúdos no texto.';setTablePanel(false);editor.focus();
  });

  const chartPanel=document.querySelector('#chartPanel'),openChart=document.querySelector('#openChart'),closeChart=document.querySelector('#closeChart'),insertChart=document.querySelector('#insertChart'),chartType=document.querySelector('#chartType'),chartTitle=document.querySelector('#chartTitle'),chartLabels=document.querySelector('#chartLabels'),chartValues=document.querySelector('#chartValues'),chartStatus=document.querySelector('#chartStatus');
  let chartInsertionPoint=0;
  const setChartPanel=(open)=>{chartPanel.hidden=!open;openChart.setAttribute('aria-expanded',String(open));if(open){chartInsertionPoint=editor.selectionStart;chartTitle.focus()}else{openChart.focus()}};
  openChart?.addEventListener('click',()=>setChartPanel(chartPanel.hidden));
  closeChart?.addEventListener('click',()=>setChartPanel(false));
  insertChart?.addEventListener('click',()=>{
    const title=cleanText(chartTitle.value),labels=chartLabels.value.split(',').map(cleanText).filter(Boolean),values=chartValues.value.split(',').map(value=>Number(value.trim().replace(',','.')));
    if(!title){chartStatus.textContent='Escreva o título do gráfico.';chartTitle.focus();return}
    if(labels.length<1||labels.length>12||labels.length!==values.length){chartStatus.textContent='Informe entre 1 e 12 categorias e a mesma quantidade de valores.';return}
    if(values.some(value=>!Number.isFinite(value)||value<0)||Math.max(...values)<=0){chartStatus.textContent='Use valores numéricos não negativos e pelo menos um valor maior que zero.';return}
    const data=labels.map((label,index)=>`${label.replace(/[;=|\[\]]/g,' ')}=${values[index]}`).join('; ');
    editor.setRangeText(`\n\n[chart: ${chartType.value}|${title.replace(/[|\[\]]/g,' ')}|${data}]\n\n`,chartInsertionPoint,chartInsertionPoint,'end');
    render();chartTitle.value='';chartLabels.value='';chartValues.value='';chartStatus.textContent='Gráfico inserido no artigo.';setChartPanel(false);editor.focus();
  });

  document.querySelector('#insertPullQuote')?.addEventListener('click',()=>{
    const start=editor.selectionStart,end=editor.selectionEnd;
    const text=window.prompt('Texto da citação em destaque:',editor.value.slice(start,end));
    if(text===null)return;
    if(!text.trim()){window.alert('Escreva o texto da citação.');return;}
    const author=window.prompt('Autor e instituição (opcional):','');
    if(author===null)return;
    const clean=value=>value.trim().replace(/[\r\n\[\]|]+/g,' ');
    editor.setRangeText('\n\n[destaque: '+clean(text)+'|'+clean(author)+']\n\n',start,end,'end');
    editor.focus();editor.dispatchEvent(new Event('input',{bubbles:true}));
  });
  editor.addEventListener('input', render);
  render();

  const titleField=document.querySelector('#titleField');
  const surfacePreview=document.querySelector('#articleSurfacePreview');
  const backgroundInputs=document.querySelectorAll('input[name="background"]');
  // Keep server-rendered tables inside the existing scrollable preview wrapper.
  const containPreviewTables=()=>{
    preview.querySelectorAll('table').forEach(table=>{
      if(table.parentElement?.matches('.preview-table-wrapper,.table-wrapper'))return;
      const wrap=document.createElement('div');
      wrap.className='preview-table-wrapper';wrap.tabIndex=0;
      wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Tabela com deslocamento horizontal');
      table.before(wrap);wrap.appendChild(table);
    });
  };
  containPreviewTables();
  new MutationObserver(containPreviewTables).observe(preview,{childList:true,subtree:true});
  const updateBackgroundPreview=()=>{
    const aged=document.querySelector('input[name="background"]:checked')?.value==='aged_paper';
    surfacePreview?.classList.toggle('article-paper',aged);
    if(surfacePreview)surfacePreview.dataset.articleBackground=aged?'aged_paper':'default';
    const heading=document.querySelector('#backgroundPreviewTitle');
    const summary=document.querySelector('#backgroundPreviewSummary');
    if(heading)heading.textContent=titleField?.value||'Título do artigo';
    if(summary)summary.textContent=document.querySelector('[name="summary"]')?.value||'';
  };
  backgroundInputs.forEach(input=>input.addEventListener('change',()=>{
    updateBackgroundPreview();
    const status=document.querySelector('#articleBackgroundStatus');
    if(status)status.textContent='Pré-visualização: '+(input.value==='aged_paper'?'Papel antigo':'Fundo padrão')+'. A escolha ainda não foi guardada.';
  }));
  titleField?.addEventListener('input',updateBackgroundPreview);
  document.querySelector('[name="summary"]')?.addEventListener('input',updateBackgroundPreview);
  updateBackgroundPreview();
  const slugField=document.querySelector('#slugField');
  const slugPreview=document.querySelector('#slugPreview');
  const slugify=(value)=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,260);
  if(slugField?.value)slugField.value=slugify(slugField.value);
  let slugWasEdited=Boolean(slugField?.value);
  const updateSlugPreview=()=>{
    if(!slugWasEdited&&slugField)slugField.value=slugify(titleField?.value||'');
    if(slugPreview)slugPreview.textContent=`URL: ${location.origin}/artigo/${slugField?.value||'gerado-a-partir-do-titulo'}`;
  };
  slugField?.addEventListener('input',()=>{slugWasEdited=true;const cursor=slugField.selectionStart;slugField.value=slugify(slugField.value);slugField.setSelectionRange(cursor,cursor);updateSlugPreview()});
  titleField?.addEventListener('input',updateSlugPreview);
  editor.closest('form')?.addEventListener('submit',()=>{
    if(slugField)slugField.value=slugify(slugField.value||titleField?.value||'artigo');
  });
  updateSlugPreview();
  const editorForm = editor.closest('form');
  const formState = () => JSON.stringify(Array.from(new FormData(editorForm)).filter(([key, value]) => typeof value === 'string' && !['csrf_token','version_token'].includes(key)));
  let initialState = formState();
  let submitting = false;
  const hasChanges = () => formState() !== initialState || Array.from(editorForm.querySelectorAll('input[type="file"]')).some(input => input.files.length);
  const updateSaveState = () => {
    const state = document.querySelector('#editorSaveState');
    if (state) state.textContent = hasChanges() ? 'Alterações por guardar' : '';
  };
  editorForm.addEventListener('editor:autosaved', event => {
    initialState = event.detail.fingerprint;
    updateSaveState();
  });
  editor.addEventListener('editor:rendered', updateSaveState);
  editorForm.addEventListener('input', updateSaveState);
  editorForm.addEventListener('change', updateSaveState);
  editorForm.addEventListener('submit', () => { submitting = true; });
  window.addEventListener('beforeunload', event => {
    if (!submitting && hasChanges()) { event.preventDefault(); event.returnValue = ''; }
  });
  document.querySelector('#useEstimatedReadingTime')?.addEventListener('click', () => {
    const input = editorForm.querySelector('input[name="read_minutes"]');
    if (input) { input.value = estimatedReadingMinutes; input.dispatchEvent(new Event('input', {bubbles:true})); }
  });

  const url=document.querySelector('#imageUrl'),file=document.querySelector('#imageFile'),image=document.querySelector('#imagePreview');
  const mode=document.querySelector('#coverMode'),coverUrl=document.querySelector('#coverVideoUrl'),coverFile=document.querySelector('#coverVideoFile');
  const coverPreview=document.querySelector('#coverPreview'),coverFields=document.querySelector('#coverVideoFields'),coverStatus=document.querySelector('#coverEditorStatus');
  const removeCover=document.querySelector('#removeCoverVideo'),removeButton=document.querySelector('#removeCoverVideoButton');
  const savedVideo=coverUrl?.value||'';
  let imageBlob='',imageObject=null,videoBlob='',videoObject=null;
  const replaceBlob=(selected,kind)=>{
    if(kind==='image'){
      if(selected!==imageObject){if(imageBlob)URL.revokeObjectURL(imageBlob);imageObject=selected;imageBlob=selected?URL.createObjectURL(selected):'';}
      return imageBlob;
    }
    if(selected!==videoObject){if(videoBlob)URL.revokeObjectURL(videoBlob);videoObject=selected;videoBlob=selected?URL.createObjectURL(selected):'';}
    return videoBlob;
  };
  const renderCoverPreview=()=>{
    if(!coverPreview||!mode)return;
    document.dispatchEvent(new CustomEvent('cover:dispose',{detail:{root:coverPreview}}));
    coverPreview.querySelectorAll(':scope > :not(#imagePreview)').forEach(el=>el.remove());
    delete coverPreview.dataset.articleCover;delete coverPreview.dataset.mode;delete coverPreview.dataset.external;coverPreview.classList.remove('is-external');coverPreview.dataset.state='idle';
    const isVideo=mode.value!=='image',selectedFile=coverFile.files[0],selectedImage=file?.files[0];
    coverFields.hidden=!isVideo;coverFile.disabled=!isVideo;
    const poster=replaceBlob(selectedImage,'image')||url?.value.trim()||coverPreview.dataset.fallback;
    image.src=poster;image.hidden=false;image.alt='Pré-visualização da imagem de capa / reserva';
    coverPreview.hidden=!isVideo&&!selectedImage&&!url?.value.trim();
    removeButton.hidden=!coverUrl.value&&!selectedFile;
    coverFile.setCustomValidity('');
    if(!isVideo){coverStatus.textContent=coverUrl.value?'Imagem estática seleccionada. O vídeo associado será conservado.':'';return;}
    let source=selectedFile?replaceBlob(selectedFile,'video'):coverUrl.value.trim();
    if(selectedFile&&(selectedFile.size>50*1024*1024||!selectedFile.size||!/\.(mp4|webm|ogg)$/i.test(selectedFile.name)||selectedFile.type&&!['video/mp4','video/webm','video/ogg','application/octet-stream'].includes(selectedFile.type))){
      const error='Use um ficheiro MP4, WebM ou OGG com até 50 MB.';coverFile.setCustomValidity(error);coverStatus.textContent=error;return;
    }
    let parsed=null;try{parsed=new URL(source);}catch{}
    if(source&&!selectedFile&&(!parsed||!['http:','https:'].includes(parsed.protocol)||parsed.username||parsed.password)){coverStatus.textContent='Use uma ligação válida de vídeo.';return;}
    const native=selectedFile||/\.(mp4|webm|ogg)$/i.test(parsed?.pathname||'');
    const owned=parsed?.protocol==='https:'&&parsed.hostname==='res.cloudinary.com'&&parsed.pathname.startsWith('/'+coverPreview.dataset.cloud+'/video/upload/');
    if(source&&native&&!selectedFile&&!owned&&(mode.value==='video_animated'||source!==savedVideo)){coverStatus.textContent='Carregue o vídeo para o Cloudinary ou use uma ligação da sua conta.';return;}
    if(!source){coverStatus.textContent='Seleccione ou carregue um vídeo; a imagem de reserva mantém-se visível.';return;}
    if(!native){
      if(mode.value==='video_animated'){coverStatus.textContent='A capa animada exige um ficheiro de vídeo da sua conta Cloudinary.';return;}
      const host=parsed.hostname.toLowerCase().replace(/^www\./,'');
      if(!['youtube.com','m.youtube.com','youtube-nocookie.com','youtu.be','vimeo.com','player.vimeo.com'].includes(host)){coverStatus.textContent='Use um vídeo do Cloudinary, YouTube ou Vimeo.';return;}
      const external=document.createElement('div');external.className='cover-external-player';external.id='cover-editor-video';
      const template=document.createElement('template');template.className='cover-external-template';template.innerHTML=videoPreview(escape(titleField?.value||'Vídeo da capa'),source);
      const start=document.createElement('button');start.type='button';start.className='cover-toggle';start.setAttribute('aria-controls',external.id);
      const restore=document.createElement('button');restore.type='button';restore.className='cover-restore';restore.textContent='Mostrar imagem de reserva';restore.hidden=true;
      coverPreview.dataset.articleCover='';coverPreview.dataset.external='true';coverPreview.dataset.mode=mode.value;coverPreview.classList.add('is-external');coverPreview.append(external,template,start,restore);document.dispatchEvent(new CustomEvent('cover:mount',{detail:{root:coverPreview}}));
      coverStatus.textContent='Pré-visualização com controlos. As alterações ainda não foram guardadas.';return;
    }
    const video=document.createElement('video');video.className='cover-video';video.id='cover-editor-video';video.dataset.src=source;video.preload='none';video.playsInline=true;video.muted=true;video.defaultMuted=true;
    video.setAttribute('aria-label','Pré-visualização do vídeo da capa');
    video.autoplay=mode.value==='video_animated';video.loop=video.autoplay;video.controls=!video.autoplay;
    const toggle=document.createElement('button');toggle.type='button';toggle.className='cover-toggle';toggle.setAttribute('aria-controls',video.id);toggle.hidden=true;
    const status=document.createElement('p');status.className='cover-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.hidden=true;
    coverPreview.dataset.articleCover='';coverPreview.dataset.mode=mode.value;
    coverPreview.append(video,toggle,status);document.dispatchEvent(new CustomEvent('cover:mount',{detail:{root:coverPreview}}));
    coverStatus.textContent='Pré-visualização local. Use Guardar artigo para concluir as alterações.';
  };
  for(const field of [url,coverUrl])field?.addEventListener('input',()=>{if(field===coverUrl)removeCover.value='';renderCoverPreview();});
  for(const field of [file,coverFile,mode])field?.addEventListener('change',()=>{if(field===coverFile||field===mode&&mode.value!=='image')removeCover.value='';renderCoverPreview();});
  removeButton?.addEventListener('click',()=>{coverUrl.value='';coverFile.value='';removeCover.value='yes';mode.value='image';replaceBlob(null,'video');mode.dispatchEvent(new Event('change',{bubbles:true}));coverStatus.textContent='Vídeo removido da capa. Use Guardar artigo para confirmar.';});
  editorForm.addEventListener('submit',()=>{if(coverFile?.files.length&&!coverFile.disabled){coverStatus.textContent='A carregar e guardar a capa. Aguarde a resposta antes de fechar a página.';coverPreview.setAttribute('aria-busy','true');}});
  window.addEventListener('pagehide',event=>{if(event.persisted)return;document.dispatchEvent(new CustomEvent('cover:dispose',{detail:{root:coverPreview}}));if(imageBlob)URL.revokeObjectURL(imageBlob);if(videoBlob)URL.revokeObjectURL(videoBlob);});
  renderCoverPreview();

})();
