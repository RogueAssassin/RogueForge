// RogueForge v0.8.5 shared visual/runtime quality layer.
(()=>{
  const previous=window.serviceLogo;
  function bestIdentity(key){
    const raw=String(key||'');
    const items=window.state?.containers||[];
    const exact=items.find(c=>c.name===raw||c.service===raw);
    if(exact)return exact.image||exact.service||exact.name||raw;
    const project=items.find(c=>c.project===raw);
    if(project)return project.image||project.service||project.name||raw;
    return raw;
  }
  if(typeof previous==='function')window.serviceLogo=serviceLogo=function(key){return previous(bestIdentity(key));};
  document.documentElement.dataset.rfQuality='085';
})();
