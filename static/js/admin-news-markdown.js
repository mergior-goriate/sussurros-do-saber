/* Toolbar de notícias: usa apenas o textarea existente, sem alterar o formulário. */
(() => {
  'use strict';
  const editor = document.getElementById('news-body');
  const toolbar = document.querySelector('.news-markdown-toolbar');
  if (!editor || !toolbar) return;

  const ask = (label, fallback = '') => window.prompt(label, fallback);
  const selected = () => editor.value.slice(editor.selectionStart, editor.selectionEnd);
  const safeUrl = url => /^https:\/\/[^\s<>"']+$/i.test(url || '');
  const insert = (content, from = editor.selectionStart, to = editor.selectionEnd) => {
    if (editor.value.length - (to - from) + content.length > editor.maxLength) {
      window.alert('O conteúdo excederia o limite permitido para a notícia.');
      return false;
    }
    editor.setRangeText(content, from, to, 'end');
    editor.dispatchEvent(new Event('input', { bubbles:true }));
    editor.focus();
    return true;
  };
  const wrap = (left, right, placeholder = 'texto') => {
    const text = selected() || placeholder;
    insert(left + text + right);
  };
  const fullLine = (prefix, fallback) => {
    const start = editor.value.lastIndexOf('\n', Math.max(0, editor.selectionStart - 1)) + 1;
    const last = editor.value.indexOf('\n', editor.selectionEnd);
    const end = last === -1 ? editor.value.length : last;
    const text = editor.value.slice(start, end) || fallback;
    insert(text.split('\n').map(line => prefix + line.replace(/^#{1,6}\s+/, '')).join('\n'), start, end);
  };
  const block = snippet => insert('\n\n' + snippet + '\n\n');
  const footnote = () => {
    const note = ask('Escreva a nota de rodapé ou referência:');
    if (!note || !note.trim()) return;
    let number = 1;
    while (editor.value.includes('[^nota-' + number + ']')) number++;
    const id = 'nota-' + number;
    const content = editor.value;
    const start = editor.selectionStart, end = editor.selectionEnd;
    const insertion = '[^' + id + ']';
    const definition = '\n\n[^' + id + ']: ' + note.trim().replace(/\r?\n/g, '\n    ');
    if (content.length + insertion.length + definition.length > editor.maxLength) {
      window.alert('O conteúdo excederia o limite permitido.'); return;
    }
    editor.setRangeText(insertion, end, end, 'end');
    editor.value += definition;
    editor.dispatchEvent(new Event('input', {bubbles:true}));
    editor.focus();
    editor.setSelectionRange(start + insertion.length, start + insertion.length);
  };
  toolbar.addEventListener('click', event => {
    const button = event.target.closest('button[data-news-md]');
    if (!button || !toolbar.contains(button)) return;
    const kind = button.dataset.newsMd;
    if (/^h[2-6]$/.test(kind)) return fullLine('#'.repeat(Number(kind[1])) + ' ', 'Título da secção');
    if (kind === 'bold') return wrap('**', '**');
    if (kind === 'italic') return wrap('*', '*');
    if (kind === 'quote') return fullLine('> ', 'Citação');
    if (kind === 'list') return fullLine('- ', 'Item');
    if (kind === 'reference') {
      const link = ask('URL HTTPS da referência:','https://');
      if (link === null) return;
      if (!safeUrl(link)) return window.alert('Introduza um URL HTTPS válido.');
      return insert('[' + (selected() || 'Referência') + '](' + link + ')');
    }
    if (kind === 'footnote') return footnote();
    if (kind === 'dropcap') {
      const position = editor.selectionStart;
      const breakAt = editor.value.lastIndexOf('\n\n', Math.max(0, position - 1));
      const from = breakAt < 0 ? 0 : breakAt + 2;
      const next = editor.value.indexOf('\n\n', position);
      const to = next < 0 ? editor.value.length : next;
      const paragraph = editor.value.slice(from, to);
      if (!paragraph.trim()) return window.alert('Escreva primeiro o parágrafo.');
      const dropcap = window.editorialDropcap, marker = dropcap.marker(paragraph);
      return insert(marker ? paragraph.slice(marker.length) : dropcap.canonical + paragraph, from, to);
    }
    if (kind === 'explainer') {
      const title = ask('Título da caixa explicativa (opcional):', '');
      if (title === null) return;
      const body = ask('Explicação:', selected() || '');
      if (body === null || !body.trim()) return;
      const layout = ask('Disposição: full (largura do texto) ou right (à direita)', 'full');
      if (layout === null) return;
      if (!['right','full'].includes(layout)) return window.alert('Escolha full ou right.');
      const cleanTitle = title.replace(/[\r\n\[\]|]/g,' ').trim();
      return insert('\n\n[caixa: ' + cleanTitle + '|' + layout + ']\n' + body.trim() + '\n[/caixa]\n\n');
    }
    if (kind === 'pullquote') {
      const quote = ask('Texto da citação em destaque:', selected() || '');
      if (!quote || !quote.trim()) return;
      const author = ask('Autoria da citação (opcional):','');
      if (author === null) return;
      return block('[destaque: ' + quote.trim().replace(/[\]\r\n|]/g,' ') + '|' + author.trim().replace(/[\]\r\n|]/g,' ') + ']');
    }
    if (kind === 'image' || kind === 'video') {
      const url = ask('URL HTTPS ' + (kind === 'image' ? 'da imagem:' : 'do vídeo:'), 'https://');
      if (url === null) return;
      if (!safeUrl(url)) return window.alert('Introduza um URL HTTPS válido.');
      const description = ask(kind === 'image' ? 'Descrição alternativa da imagem:' : 'Título do vídeo:', kind === 'image' ? '' : 'Vídeo');
      if (description === null || !description.trim()) return window.alert('É necessária uma descrição.');
      return block(kind === 'image'
        ? '![' + description.replace(/[\]\r\n]/g, ' ') + '](' + url + ')'
        : '[video: ' + description.replace(/[\]\r\n]/g, ' ') + '](' + url + ')');
    }
    if (kind === 'table') return block('| Coluna 1 | Coluna 2 |\n| --- | --- |\n| Valor 1 | Valor 2 |');
    if (kind === 'chart') return block('[chart: bar|Título do gráfico|Grupo A=12;Grupo B=8]');
  });
})();
