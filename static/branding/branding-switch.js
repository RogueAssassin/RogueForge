(()=>{
  // Settings > Branding & appearance. "mark" is the 2.4 clean monogram; "base", "dark" and "light"
  // keep the original artwork available for anyone who prefers it.
  const variants={mark:'/branding/rogueforge-mark.svg',base:'/branding/rogueforge.svg',dark:'/branding/rogueforge-dark.svg',light:'/branding/rogueforge-light.svg'};
  const labels={mark:'Monogram',base:'Classic',dark:'Classic dark',light:'Classic light'};
  const key='rogueforge-brand-variant',themeKey='rogueforge-theme',themes={system:'System',dark:'Dark',light:'Light'};
  const read=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
  const write=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
  // Before 2.4 the default was stored as "base"; move those users onto the new default once.
  function current(){let v=read(key);if(!v||(v==='base'&&!read(key+'-v24'))){v='mark';write(key+'-v24','1')}return variants[v]?v:'mark'}
  function apply(name){
    if(!variants[name])name='mark';write(key,name);document.documentElement.dataset.rfBrand=name;
    document.querySelectorAll('[data-rf-brand-image]').forEach(img=>img.src=variants[name]);
    document.querySelectorAll('.rf-brand-crop').forEach(el=>{el.style.backgroundImage=`url("${variants[name]}")`;el.style.backgroundSize='cover';el.style.backgroundPosition='center'});
    const icon=document.querySelector('link[rel="icon"]');if(icon)icon.href=variants[name];
    document.querySelectorAll('[data-rf-brand-choice]').forEach(b=>b.classList.toggle('active',b.dataset.rfBrandChoice===name));
  }
  function currentTheme(){const t=read(themeKey);return themes[t]?t:'system'}
  function applyTheme(name){
    if(!themes[name])name='system';write(themeKey,name);
    if(name==='system')delete document.documentElement.dataset.theme;else document.documentElement.dataset.theme=name;
    const dark=name==='dark'||(name==='system'&&!matchMedia('(prefers-color-scheme: light)').matches);
    document.querySelectorAll('meta[name="theme-color"]').forEach(m=>m.content=dark?'#1f1e1d':'#faf9f5');
    document.querySelectorAll('[data-rf-theme-choice]').forEach(b=>b.classList.toggle('active',b.dataset.rfThemeChoice===name));
  }
  function controls(){
    if(document.querySelector('.rf-brand-switch'))return;
    const settings=document.querySelector('#view-settings');if(!settings)return;
    const box=document.createElement('section');box.className='section-card rf-brand-switch';
    box.innerHTML='<header class="section-head"><div><p class="eyebrow">Appearance</p><h3>Theme and identity</h3></div></header>'
      +'<p class="rf-brand-help">Theme follows your operating system unless you choose one here. Saved in this browser only.</p>'
      +'<div class="rf-theme-options" role="group" aria-label="Theme">'+Object.keys(themes).map(t=>`<button type="button" class="small-button" data-rf-theme-choice="${t}">${themes[t]}</button>`).join('')+'</div>'
      +'<p class="rf-brand-help rf-brand-help-icon">Icon used in the sidebar and browser tab.</p>'
      +'<div class="rf-brand-preview"><img data-rf-brand-image alt="RogueForge logo preview"></div>'
      +'<div class="rf-brand-options" role="group" aria-label="Icon">'+Object.keys(variants).map(v=>`<button type="button" class="small-button" data-rf-brand-choice="${v}">${labels[v]}</button>`).join('')+'</div>';
    settings.appendChild(box);
    box.addEventListener('click',e=>{const b=e.target.closest('[data-rf-brand-choice]');if(b)apply(b.dataset.rfBrandChoice);const t=e.target.closest('[data-rf-theme-choice]');if(t)applyTheme(t.dataset.rfThemeChoice)});
    apply(current());applyTheme(currentTheme());
  }
  matchMedia('(prefers-color-scheme: light)').addEventListener?.('change',()=>applyTheme(currentTheme()));
  document.addEventListener('DOMContentLoaded',()=>{apply(current());applyTheme(currentTheme());controls()});
  new MutationObserver(()=>controls()).observe(document.documentElement,{childList:true,subtree:true});
  if(document.readyState!=='loading'){apply(current());applyTheme(currentTheme());controls()}
})();
