(()=>{
 const search=document.querySelector('#journal-admin-search'),filter=document.querySelector('#journal-admin-filter'),rows=[...document.querySelectorAll('[data-journal-row]')];
 const normalize=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const updateList=()=>{const query=normalize(search?.value||''),state=filter?.value||'all';let count=0;rows.forEach(row=>{row.hidden=!normalize(row.textContent).includes(query)||(state!=='all'&&row.dataset.state!==state);if(!row.hidden)count++;});const output=document.querySelector('#journal-admin-count');if(output)output.textContent=count+' de '+rows.length+' revistas';const empty=document.querySelector('#journal-admin-empty');if(empty)empty.hidden=count>0;};
 search?.addEventListener('input',updateList);filter?.addEventListener('change',updateList);if(search)updateList();
 const form=document.querySelector('.journal-editor');if(!form)return;
 const area=form.querySelector('[name="content_markdown"]'),references=form.querySelector('[name="references"]'),preview=form.querySelector('[data-md-preview]'),refPreview=form.querySelector('[data-reference-preview]'),status=document.querySelector('#journal-editor-status'),count=document.querySelector('#journal-word-count');
 let dirty=false,timer,controller;
 const markDirty=()=>{dirty=true;status.textContent='Alterações por guardar.';};
 form.addEventListener('input',markDirty);form.addEventListener('change',markDirty);
 form.addEventListener('submit',()=>{dirty=false;status.textContent='A guardar…';});
 window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
 const authorsEditor=form.querySelector('#journal-authors-editor'),authorTemplate=form.querySelector('#journal-author-template');
 form.querySelector('#journal-add-author')?.addEventListener('click',()=>{
   if(authorsEditor.querySelectorAll('[data-author-card]').length>=30){status.textContent='Limite de 30 autores por artigo.';return;}
   const fragment=authorTemplate.content.cloneNode(true);
   const input=fragment.querySelector('[name="author_name"]');
   authorsEditor.appendChild(fragment);markDirty();input.focus();
 });
 authorsEditor?.addEventListener('click',event=>{
   const remove=event.target.closest('[data-remove-author]');if(!remove)return;
   remove.closest('[data-author-card]').remove();markDirty();
   form.querySelector('#journal-add-author').focus();
 });
 const render=async()=>{
   const text=area.value.trim();count.textContent=(text?text.split(/\s+/).length:0)+' palavras · '+area.value.length+' caracteres';
   controller?.abort();controller=new AbortController();const data=new FormData();data.set('csrf_token',form.querySelector('[name="csrf_token"]').value);data.set('content',area.value);data.set('references',references.value);form.querySelectorAll('.journal-article-field').forEach(field=>{if(!['content_markdown','references'].includes(field.name))data.set(field.name,field.value);});
   try{const response=await fetch(form.dataset.previewUrl,{method:'POST',body:data,signal:controller.signal});if(!response.ok)throw new Error();const result=await response.json();preview.innerHTML=result.html||'<p>O conteúdo aparecerá aqui.</p>';refPreview.innerHTML=result.references||'<p>Sem referências adicionadas.</p>';}
   catch(error){if(error.name!=='AbortError'){preview.textContent='Não foi possível atualizar a pré-visualização. O texto continua no editor.';}}
 };
 const schedule=()=>{clearTimeout(timer);timer=setTimeout(render,450);};
 form.querySelectorAll('.journal-article-field').forEach(field=>field.addEventListener('input',schedule));render();
 const snippets={heading:'# Título do artigo',section:'## Secção',quote:'> Citação',list:'- Item',reference:'[Referência](https://doi.org/...)',image:'![Descrição da imagem](https://...)',video:'[video: Título do vídeo](https://www.youtube.com/watch?v=...)',table:'| Coluna | Coluna |\n| --- | --- |\n| Valor | Valor |',chart:'[chart: bar|Título do gráfico|Grupo A=12; Grupo B=8]'};
 form.querySelectorAll('[data-md]').forEach(button=>button.addEventListener('click',()=>{
   const type=button.dataset.md,start=area.selectionStart,end=area.selectionEnd,selected=area.value.slice(start,end)||'texto';
   if(type==='dropcap'){
     const paragraphStart=area.value.lastIndexOf('\n\n',Math.max(0,start-1))+2;
     const from=paragraphStart===1?0:paragraphStart;
     const next=area.value.indexOf('\n\n',start);
     const to=next<0?area.value.length:next;
     const paragraph=area.value.slice(from,to);
     if(!paragraph.trim()){window.alert('Escreva primeiro o parágrafo.');return;}
     const dropcap=window.editorialDropcap,marker=dropcap.marker(paragraph);
     const value=marker?paragraph.slice(marker.length):dropcap.canonical+paragraph;
     area.setRangeText(value,from,to,'end');area.focus();markDirty();schedule();return;
   }
   if(type==='link'){
     const label=window.prompt('Texto da hiperligação:',area.value.slice(start,end)||'');
     if(label===null)return;
     if(!label.trim()){window.alert('Escreva o texto da hiperligação.');return;}
     const address=window.prompt('Endereço da hiperligação (https://…):','https://');
     if(address===null)return;
     let url;
     try{url=new URL(address.trim());if(!['https:','http:'].includes(url.protocol)||!url.hostname)throw new Error();}
     catch{window.alert('Informe um endereço válido iniciado por https:// ou http://.');return;}
     const text=label.trim().replace(/\\/g,'\\\\').replace(/\[/g,'\\[').replace(/\]/g,'\\]').replace(/[\r\n]+/g,' ');
     const href=url.href.replace(/\(/g,'%28').replace(/\)/g,'%29');
     area.setRangeText('['+text+']('+href+')',start,end,'end');
     area.focus();markDirty();schedule();return;
   }
   let value=type==='bold'?'**'+selected+'**':type==='italic'?'*'+selected+'*':snippets[type]||'';
   if(!['bold','italic'].includes(type))value='\n\n'+value+'\n\n';
   area.setRangeText(value,start,end,'end');area.focus();markDirty();schedule();
 }));
 const image=document.querySelector('#journal-cover-preview'),upload=form.querySelector('[name="cover_file"]'),url=form.querySelector('[name="cover_image"]');
 upload.addEventListener('change',()=>{const file=upload.files[0];if(file){const reader=new FileReader();reader.addEventListener('load',()=>{image.src=reader.result;image.hidden=false;});reader.readAsDataURL(file);}});
 url.addEventListener('change',()=>{if(upload.files.length)return;const value=url.value.trim();if(/^https?:\/\//i.test(value)){image.src=value;image.hidden=false;}else image.hidden=true;});
})();
