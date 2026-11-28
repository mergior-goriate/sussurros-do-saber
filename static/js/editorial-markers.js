/* The grammar is supplied by editorial_content.py, not duplicated in editors. */
(() => {
  const pattern = document.querySelector('meta[name="editorial-dropcap-pattern"]')?.content;
  if (!pattern) return;
  const start = new RegExp('^' + pattern + '(?=[ \\t\\r\\n]|$)[ \\t]*', 'i');
  const lines = new RegExp('^' + pattern + '(?=[ \\t\\r\\n]|$)[ \\t]*', 'gim');
  window.editorialDropcap = Object.freeze({
    canonical: '[capitular] ',
    marker: text => text.match(start)?.[0] || '',
    withoutMarkers: text => text.replace(lines, ''),
  });
})();
