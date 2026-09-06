// RogueForge canonical live logs and terminal UI.
// Live logs remain intentionally browser-buffered: RogueForge does not build a server-side
// log database/index, so idle CPU/RAM remains effectively unchanged.
const RF_LOG_MAX_LINES = 3000;
const rfLive = { source: null, terminalToken: null, terminalCursor: 0, terminalTimer: null, paused: false, lines: [], pending: [], renderFrame: 0 };

function liveButton(label, attrName, container, className="") { return `<button class="small-button ${className}" ${attrName}="${container.id}" data-name="${attr(container.name)}">${label}</button>`; }
const previousRenderContainers = renderContainers;
renderContainers = function renderContainersWithLiveOps() {
  previousRenderContainers();
  state.containers.forEach(container => {
    const row = document.querySelector(`[data-container-select="${CSS.escape(container.id)}"]`)?.closest('.container-row');
    if (!row) return;
    const actions = row.querySelector('.rf-action-secondary');
    if (!actions || actions.querySelector('[data-live-logs]')) return;
    actions.insertAdjacentHTML('beforeend', liveButton('Live logs','data-live-logs',container,'accent') + (container.state==='running' ? liveButton('Terminal','data-terminal',container,'') : ''));
  });
};
function stopLiveLogs() {
  if (rfLive.source) { rfLive.source.close(); rfLive.source=null; }
  if (rfLive.renderFrame) { cancelAnimationFrame(rfLive.renderFrame); rfLive.renderFrame=0; }
  rfLive.pending=[];
  const s=$('#liveLogStatus'); if(s)s.textContent='Disconnected';
}
function classifyLiveLine(line){
  const v=line.toLowerCase();
  if(/\b(error|fatal|panic|exception|failed|failure)\b/.test(v))return 'error';
  if(/\b(warn|warning)\b/.test(v))return 'warn';
  return 'info';
}
function flushLiveLines(){
  rfLive.renderFrame=0;
  if(rfLive.pending.length){
    rfLive.lines.push(...rfLive.pending);rfLive.pending=[];
    if(rfLive.lines.length>RF_LOG_MAX_LINES)rfLive.lines.splice(0,rfLive.lines.length-RF_LOG_MAX_LINES);
  }
  if(!rfLive.paused)renderLiveLines();
}
function queueLiveLine(line){
  rfLive.pending.push(String(line));
  if(!rfLive.renderFrame)rfLive.renderFrame=requestAnimationFrame(flushLiveLines);
}
function renderLiveLines(){
  const filter=($('#liveLogSearch')?.value||'').trim().toLowerCase();
  const output=filter?rfLive.lines.filter(line=>line.toLowerCase().includes(filter)):rfLive.lines;
  const pre=$('#liveLogText');if(!pre)return;
  const pinned=pre.scrollHeight-pre.scrollTop-pre.clientHeight<80;
  pre.textContent=output.join('\n');
  if(pinned||!filter)pre.scrollTop=pre.scrollHeight;
  const errors=output.reduce((n,line)=>n+(classifyLiveLine(line)==='error'),0);
  const warnings=output.reduce((n,line)=>n+(classifyLiveLine(line)==='warn'),0);
  const status=$('#liveLogStatus');
  if(status&&!rfLive.paused)status.textContent=`Live · ${output.length} lines${errors?` · ${errors} errors`:''}${warnings?` · ${warnings} warnings`:''}`;
}
function openLiveLogs(id,name){
  if(!ensureAuthenticated())return;
  stopLiveLogs();rfLive.lines=[];rfLive.pending=[];rfLive.paused=false;
  $('#liveLogsTitle').textContent=`${name} · Live logs`;
  $('#liveLogText').textContent='Connecting…';$('#liveLogStatus').textContent='Connecting';$('#pauseLiveLogs').textContent='Pause';$('#liveLogsDialog').showModal();
  const source=new EventSource(`/api/containers/${id}/logs/stream`);rfLive.source=source;
  source.addEventListener('ready',()=>{$('#liveLogStatus').textContent='Live';$('#liveLogText').textContent='';});
  source.addEventListener('ended',()=>{flushLiveLines();source.close();if(rfLive.source===source)rfLive.source=null;$('#liveLogStatus').textContent='Stream ended';});
  source.onmessage=event=>{try{const data=JSON.parse(event.data);queueLiveLine(data.line??event.data);}catch{queueLiveLine(event.data);}};
  source.onerror=()=>{if(rfLive.source===source)$('#liveLogStatus').textContent='Reconnecting…';};
}
async function closeTerminal(){if(rfLive.terminalTimer){clearTimeout(rfLive.terminalTimer);rfLive.terminalTimer=null;}const token=rfLive.terminalToken;rfLive.terminalToken=null;if(token&&state.auth?.authenticated){try{await api(`/api/terminal/${encodeURIComponent(token)}`,protectedOptions({method:'DELETE'}));}catch(_){}}}
async function pollTerminal(){const token=rfLive.terminalToken;if(!token)return;try{const data=await api(`/api/terminal/${encodeURIComponent(token)}?cursor=${rfLive.terminalCursor}`);rfLive.terminalCursor=data.cursor??rfLive.terminalCursor;if(data.output){const pre=$('#terminalText');pre.textContent+=data.output;pre.scrollTop=pre.scrollHeight;}$('#terminalStatus').textContent=data.closed?`Closed${data.exitCode!=null?` (${data.exitCode})`:''}`:`${data.shell||'shell'} · connected`;if(!data.closed&&token===rfLive.terminalToken)rfLive.terminalTimer=setTimeout(pollTerminal,500);}catch(error){$('#terminalStatus').textContent=error.message;}}
async function openTerminal(id,name){if(!ensureAuthenticated())return;await closeTerminal();$('#terminalTitle').textContent=`${name} · Terminal`;$('#terminalText').textContent='Opening shell…\n';$('#terminalStatus').textContent='Connecting';$('#terminalInput').value='';$('#terminalDialog').showModal();try{const data=await api(`/api/containers/${id}/terminal`,protectedOptions({method:'POST'}));rfLive.terminalToken=data.token;rfLive.terminalCursor=0;$('#terminalText').textContent='';$('#terminalStatus').textContent=`${data.shell} · connected`;pollTerminal();setTimeout(()=>$('#terminalInput').focus(),50);}catch(error){$('#terminalText').textContent=error.message;$('#terminalStatus').textContent='Failed';}}
async function sendTerminalInput(){const token=rfLive.terminalToken;if(!token)return;const input=$('#terminalInput');const value=input.value;if(!value)return;input.value='';const pre=$('#terminalText');pre.textContent+=`$ ${value}\n`;pre.scrollTop=pre.scrollHeight;try{await api(`/api/terminal/${encodeURIComponent(token)}/input`,protectedOptions({method:'POST',body:JSON.stringify({input:value+'\n'})}));}catch(error){pre.textContent+=`\n[error] ${error.message}\n`;}}
function downloadLiveLogs(){flushLiveLines();const blob=new Blob([rfLive.lines.join('\n')+'\n'],{type:'text/plain'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`rogueforge-logs-${new Date().toISOString().replace(/[:.]/g,'-')}.log`;a.click();URL.revokeObjectURL(url);}
document.addEventListener('click',event=>{
  const live=event.target.closest('[data-live-logs]');if(live)openLiveLogs(live.dataset.liveLogs,live.dataset.name);
  const terminal=event.target.closest('[data-terminal]');if(terminal)openTerminal(terminal.dataset.terminal,terminal.dataset.name);
  if(event.target.closest('#pauseLiveLogs')){rfLive.paused=!rfLive.paused;$('#pauseLiveLogs').textContent=rfLive.paused?'Resume':'Pause';if(!rfLive.paused)flushLiveLines();else $('#liveLogStatus').textContent='Paused · buffering';}
  if(event.target.closest('#clearLiveLogs')){rfLive.lines=[];rfLive.pending=[];renderLiveLines();}
  if(event.target.closest('#downloadLiveLogs'))downloadLiveLogs();
  if(event.target.closest('#terminalSend'))sendTerminalInput();
});
let rfLogFilterTimer=0;
document.addEventListener('input',event=>{if(event.target.id==='liveLogSearch'){clearTimeout(rfLogFilterTimer);rfLogFilterTimer=setTimeout(renderLiveLines,120);}});
document.addEventListener('keydown',event=>{if(event.target.id==='terminalInput'&&event.key==='Enter'){event.preventDefault();sendTerminalInput();}});
$('#liveLogsDialog')?.addEventListener('close',stopLiveLogs);$('#terminalDialog')?.addEventListener('close',closeTerminal);window.addEventListener('beforeunload',()=>{stopLiveLogs();closeTerminal();});if(state?.containers?.length)renderContainers();
