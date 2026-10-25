const $ = selector => document.querySelector(selector);
const token = $('[name=csrfmiddlewaretoken]').value;
const form = $('#generator');
let tracks = [], busy = false, polling = false, rendered = '';
async function api(url, data) {
  const response = await fetch(url, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':token},body:JSON.stringify(data)});
  let body;
  try { body = await response.json(); } catch { throw new Error(`The server could not complete this request (HTTP ${response.status}). Please retry.`); }
  if (!response.ok) throw new Error(typeof body.error === 'string' ? body.error : body.error ? JSON.stringify(body.error) : 'The request could not be completed.');
  return body;
}
function el(tag, text, className) {const e=document.createElement(tag); if(text)e.textContent=text; if(className)e.className=className; return e;}
function show(text) {$('#message').textContent=text; $('#message').hidden=false;}
function storageGet(key) {try{return sessionStorage.getItem(key);}catch{return null;}}
function storageSet(key,value) {try{sessionStorage.setItem(key,value);}catch{/* Draft storage is optional. */}}
function draft() {if(!form)return; const d=Object.fromEntries(new FormData(form)); d.instrumental=$('#instrumental').checked; storageSet('sonora-draft',JSON.stringify(d));}
function applyDraft(d) {for(const k of ['title','prompt','lyrics','duration','bpm','seed'])if(d[k]!==undefined)$('#'+k).value=d[k]; $('#instrumental').checked=!!d.instrumental; $('#lyrics-area').hidden=!!d.instrumental;}
function card(t) {
  const c=el('article',null,'track'); const top=el('div',null,'track-top'); top.append(el('div','♫','art'));
  const info=el('div'); info.append(el('h3',t.title),el('span',`${t.duration}s · ${t.bpm} BPM · ${t.instrumental?'Instrumental':'Vocals'}`,'state'));top.append(info);c.append(top,el('p',t.prompt));
  if(t.audio){const audio=el('audio');audio.controls=true;audio.preload='none';audio.src=t.audio;c.append(audio);}else c.append(el('p',t.status==='running'?'◌ Creating your sound…':t.status==='failed'?'Generation needs attention':t.status,'state'));
  if(t.error){const d=el('details');d.append(el('summary','View generation details'),el('p',t.error,'error'));c.append(d);}
  if(t.lyrics){const d=el('details');const lyrics=el('p',t.lyrics);lyrics.style.whiteSpace='pre-wrap';d.append(el('summary','Read lyrics'),lyrics);c.append(d);}
  const actions=el('div',null,'track-actions');
  if(t.audio){const link=el('a','↓ Download');link.href=t.audio+'?download=1';actions.append(link);}
  const reuse=el('button','↗ Reuse idea');reuse.type='button';reuse.onclick=()=>{storageSet('sonora-draft',JSON.stringify(t));if(form){applyDraft(t);form.scrollIntoView({behavior:'smooth'});}else location.assign('/');};actions.append(reuse);
  const del=el('button','Delete','delete');del.type='button';del.onclick=async()=>{if(!window.confirm(`Delete “${t.title}” and its audio?`))return;del.disabled=true;try{await api(`/api/tracks/${t.id}/delete/`,{});await load();}catch(e){show(e.message);del.disabled=false;}};actions.append(del);c.append(actions);return c;
}
function render() {
  const query=($('#search')?.value||'').toLocaleLowerCase();const status=$('#status-filter')?.value||'all';
  let visible=tracks.filter(t=>(status==='all'||t.status===status)&&`${t.title} ${t.prompt} ${t.lyrics}`.toLocaleLowerCase().includes(query));
  $('#count').textContent=tracks.length;$('#library-count').textContent=`${tracks.length} ${tracks.length===1?'track':'tracks'}`;
  if(form)visible=visible.slice(0,3);
  const signature=JSON.stringify(visible);if(signature===rendered)return;rendered=signature;
  $('#tracks').replaceChildren(...visible.map(card));
  if(!visible.length){const empty=el('div',null,'empty');const inner=el('div');inner.append(el('div','♫','empty-icon'),el('h3',tracks.length?'No tracks match that feeling.':'Your next favorite starts here.'),el('p',tracks.length?'Try another search or choose a different status.':'A blank canvas for your sound. Create your first track and make this space yours.'));if(!tracks.length){const link=el('a','Create your first track ↗');link.href='/';inner.append(link);}empty.append(inner);$('#tracks').append(empty);}
}
async function load(){try{const data=await api('/api/tracks/');tracks=data.tracks;render();return tracks;}catch(e){show(e.message);return [];}}
if(form){
  $('#instrumental').onchange=()=>{$('#lyrics-area').hidden=$('#instrumental').checked;draft();};
  try{const saved=storageGet('sonora-draft');if(saved)applyDraft(JSON.parse(saved));}catch{/* Ignore an invalid draft. */}
  form.addEventListener('input',draft);
  document.querySelectorAll('[data-prompt]').forEach(button=>{button.setAttribute('aria-pressed','false');button.onclick=()=>{$('#prompt').value=button.dataset.prompt;document.querySelectorAll('[data-prompt]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',String(b===button));});draft();};});
  form.onsubmit=async event=>{event.preventDefault();if(busy)return;busy=true;$('#generate').disabled=true;$('#generate').textContent='◌ Sending your idea…';$('#message').hidden=true;const data=Object.fromEntries(new FormData(form));data.instrumental=$('#instrumental').checked;try{await api('/api/generate/',data);show('Your track is generating. Find it in Your library while you keep creating.');}catch(e){show(e.message);}finally{busy=false;$('#generate').disabled=false;$('#generate').replaceChildren(document.createTextNode('✦ Generate music '),el('span','↗'));await load();}};
}
$('#search')?.addEventListener('input',render);$('#status-filter')?.addEventListener('change',render);
if($('#refresh'))$('#refresh').onclick=async()=>{const b=$('#refresh');b.disabled=true;try{await tick();}finally{b.disabled=false;}};
async function tick(){if(polling||document.hidden)return;polling=true;try{const current=await load();for(const t of current.filter(t=>t.status==='running')){try{await api(`/api/tracks/${t.id}/status/`,{});}catch{/* Track details contain the saved error. */}}if(current.some(t=>t.status==='running'))await load();}finally{polling=false;}}
async function health(){try{const d=await api('/api/health/');$('#connection').textContent=d.connected?'● Engine ready':'○ Engine not connected';$('#connection').classList.toggle('online',d.connected);if($('#engine-note')){$('#engine-note').hidden=d.connected;$('#engine-status-detail').textContent=d.message||'';}}catch{$('#connection').textContent='○ Connection unavailable';}}
load();health();setInterval(tick,10000);setInterval(()=>{if(!document.hidden)health();},30000);
