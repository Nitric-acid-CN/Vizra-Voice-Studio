() => {
  const root = document.querySelector('gradio-app')?.shadowRoot || document;
  if (window.__vizraSegmentPlayer) return [];
  const player = new Audio(), drafts = new Map();
  window.__vizraSegmentPlayer = player;
  function key(row) {return row.closest('.segment-grid').dataset.project + ':' + row.dataset.segment;}
  function sync() {
    root.querySelectorAll('.segment-grid tr[data-segment]').forEach(row => {
      const text = row.querySelector('textarea'), draft = drafts.get(key(row));
      if (text && draft !== undefined) {
        if (draft === text.defaultValue) drafts.delete(key(row));
        else if (text.value !== draft) text.value = draft;
      }
      const button = row.querySelector('button[data-action="play"]');
      if (!button) return;
      const playing = button.dataset.src && new URL(button.dataset.src,location.href).href === player.src && !player.paused && !player.ended;
      const label = playing ? '❚❚ 暂停' : '▶ 试听';
      if (button.textContent !== label) button.textContent = label;
      button.setAttribute('aria-pressed', playing ? 'true' : 'false');
    });
  }
  function send(row, action, version) {
    const id = action === 'version' ? '#segment-row-edit' : '#segment-row-redo';
    const input = root.querySelector(id + ' textarea, ' + id + ' input');
    const data = {index:Number(row.dataset.segment),action,version,token:row.dataset.token,text:row.querySelector('textarea')?.value || '',nonce:Date.now()+Math.random()};
    const prototype = input.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(prototype,'value').set.call(input,JSON.stringify(data));
    input.dispatchEvent(new Event('input',{bubbles:true,composed:true}));
  }
  ['play','pause','ended','error'].forEach(event => player.addEventListener(event,sync));
  new MutationObserver(sync).observe(root,{childList:true,subtree:true});
  root.addEventListener('input',event => {
    const text=event.composedPath().find(el=>el?.matches?.('.segment-grid textarea'));
    if (text) drafts.set(key(text.closest('tr')),text.value);
  });
  root.addEventListener('change',event => {
    const select=event.composedPath().find(el=>el?.matches?.('.segment-grid select[data-action="version"]'));
    if (!select) return;
    const row=select.closest('tr');drafts.delete(key(row));send(row,'version',select.value);
  });
  root.addEventListener('click',async event => {
    const button=event.composedPath().find(el=>el?.matches?.('.segment-grid button[data-action]'));
    if (!button || button.disabled) return;
    const row=button.closest('tr');
    if (button.dataset.action==='play') {
      const source=new URL(button.dataset.src,location.href).href;
      if (source===player.src && !player.paused) player.pause();
      else {if(source!==player.src)player.src=source;try{await player.play()}catch(e){console.warn(e.message)}}
      sync();return;
    }
    button.disabled=true;button.dataset.pending='true';
    row.querySelector('.row-status').innerHTML='<span class="row-spinner"></span> 等待中';
    send(row,'redo');
  });
  window.addEventListener('vizra-row-done',() => {
    root.querySelectorAll('.segment-grid button[data-pending]').forEach(button=>{button.disabled=false;delete button.dataset.pending;});
  });
  window.addEventListener('vizra-stop',() => {
    root.querySelectorAll('.segment-grid tr[data-segment]').forEach(row=>{
      if(!row.querySelector('.row-spinner'))return;
      row.querySelector('.row-status').textContent='已停止';row.querySelector('textarea').readOnly=false;
      row.querySelector('button[data-action="redo"]').disabled=false;
      const select=row.querySelector('select');if(select&&select.options[0]?.value!=='—')select.disabled=false;
    });
  });
  return [];
}
