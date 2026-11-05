(()=>{
  // Settings > Appearance: theme (System/Light/Dark, handled by the shared rogue-theme.js kit)
  // plus the original RogueForge icon variants.
  const variants={base:'/branding/rogueforge.svg',dark:'/branding/rogueforge-dark.svg',light:'/branding/rogueforge-light.svg'};
  const labels={base:'Base',dark:'Dark',light:'Light'};
  const key='rogueforge-brand-variant',themes={system:'System',light:'Light',dark:'Dark'};
  const read=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
  const write=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
  function current(){const v=read(key);return variants[v]?v:'base'}
  function apply(name){
    if(!variants[name])name='base';write(key,name);document.documentElement.dataset.rfBrand=name;
    document.querySelectorAll('[data-rf-brand-image]').forEach(img=>img.src=variants[name]);
    document.querySelectorAll('.rf-brand-crop').forEach(el=>{el.style.backgroundImage=`url("${variants[name]}")`;el.style.backgroundSize='cover';el.style.backgroundPosition='center'});
    const icon=document.querySelector('link[rel="icon"]');if(icon)icon.href=variants[name];
    document.querySelectorAll('[data-rf-brand-choice]').forEach(b=>b.classList.toggle('active',b.dataset.rfBrandChoice===name));
  }
  function controls(){
    if(document.querySelector('.rf-brand-switch'))return;
    const settings=document.querySelector('#view-settings');if(!settings)return;
    const box=document.createElement('section');box.className='section-card rf-brand-switch';
    box.innerHTML='<header class="section-head"><div><p class="eyebrow">Appearance</p><h3>Theme and identity</h3></div></header>'
      +'<p class="rf-brand-help">System follows your device. The same choice is in the theme menu at the top right, and is saved in this browser only.</p>'
      +'<div class="rf-theme-options" role="group" aria-label="Theme">'+Object.keys(themes).map(t=>`<button type="button" class="small-button" data-rogue-theme-choice="${t}">${themes[t]}</button>`).join('')+'</div>'
      +'<p class="rf-brand-help rf-brand-help-icon">Icon used in the sidebar and browser tab.</p>'
      +'<div class="rf-brand-preview"><img data-rf-brand-image alt="RogueForge logo preview"></div>'
      +'<div class="rf-brand-options" role="group" aria-label="Icon">'+Object.keys(variants).map(v=>`<button type="button" class="small-button" data-rf-brand-choice="${v}">${labels[v]}</button>`).join('')+'</div>';
    settings.appendChild(box);
    box.addEventListener('click',e=>{const b=e.target.closest('[data-rf-brand-choice]');if(b)apply(b.dataset.rfBrandChoice)});
    apply(current());
    if(window.RogueTheme)window.RogueTheme.setDefault('system');
  }
  document.addEventListener('DOMContentLoaded',()=>{apply(current());controls()});
  new MutationObserver(()=>controls()).observe(document.documentElement,{childList:true,subtree:true});
  if(document.readyState!=='loading'){apply(current());controls()}
})();
