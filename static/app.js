const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let currentStack=null;
async function api(path, opts={}) {
  const r=await fetch(path,{headers:{'content-type':'application/json'},...opts});
  const data=await r.json();
  if(!r.ok) throw new Error(data.error||data.output||`HTTP ${r.status}`);
  return data;
}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function load(){
  try{
    const [status,stacks,containers]=await Promise.all([api('/api/status'),api('/api/stacks'),api('/api/containers')]);
    $('#engine').textContent=`${status.engine.toUpperCase()} · ${status.socket}`;
    $('#engineVersion').textContent=status.version; $('#stackCount').textContent=stacks.length; $('#containerCount').textContent=containers.length; $('#runningCount').textContent=containers.filter(x=>x.state==='running').length;
    $('#stackGrid').innerHTML=stacks.map(s=>`<article class="card"><div class="card-head"><div><h3>${esc(s.name)}</h3><div class="muted">${esc(s.composeFile)}</div></div><span class="badge">${esc(s.engineHint)}</span></div><div class="actions"><button onclick="stackAction('${esc(s.name)}','start')">Start</button><button onclick="stackAction('${esc(s.name)}','stop')">Stop</button><button onclick="stackAction('${esc(s.name)}','restart')">Restart</button><button onclick="stackAction('${esc(s.name)}','pull')">Pull</button><button onclick="editStack('${esc(s.name)}')">Compose</button></div></article>`).join('');
    $('#containerGrid').innerHTML=containers.map(c=>`<article class="card"><div class="card-head"><div><h3>${esc(c.name)}</h3><div class="muted">${esc(c.image)}</div></div><span class="badge ${c.state==='running'?'running':''}">${esc(c.state)}</span></div><div class="muted" style="margin-top:8px">${esc(c.status)}</div><div class="actions"><button onclick="containerAction('${c.id}','start')">Start</button><button onclick="containerAction('${c.id}','stop')">Stop</button><button onclick="containerAction('${c.id}','restart')">Restart</button><button onclick="showLogs('${c.id}','${esc(c.name)}')">Logs</button></div></article>`).join('');
  }catch(e){$('#engine').textContent=`ERROR · ${e.message}`}
}
async function stackAction(name,action){if(!confirm(`${action} ${name}?`))return;try{await api(`/api/stacks/${encodeURIComponent(name)}/${action}`,{method:'POST'});await load()}catch(e){alert(e.message)}}
async function containerAction(id,action){try{await api(`/api/containers/${id}/${action}`,{method:'POST'});setTimeout(load,800)}catch(e){alert(e.message)}}
async function editStack(name){try{const d=await api(`/api/stacks/${encodeURIComponent(name)}/compose`);currentStack=name;$('#editorTitle').textContent=`${name} · ${d.name}`;$('#composeText').value=d.content;$('#editor').showModal()}catch(e){alert(e.message)}}
$('#saveCompose').addEventListener('click',async()=>{try{await api(`/api/stacks/${encodeURIComponent(currentStack)}/compose`,{method:'PUT',body:JSON.stringify({content:$('#composeText').value})});$('#editor').close();alert('Compose validated and saved.')}catch(e){alert(e.message)}})
async function showLogs(id,name){try{const d=await api(`/api/containers/${id}/logs`);$('#logsTitle').textContent=`${name} · logs`;$('#logText').textContent=d.logs;$('#logs').showModal()}catch(e){alert(e.message)}}
$$('.tabs button').forEach(b=>b.onclick=()=>{$$('.tabs button').forEach(x=>x.classList.toggle('active',x===b));$$('.panel').forEach(x=>x.classList.toggle('active',x.id===b.dataset.tab))})
load();setInterval(load,15000);
