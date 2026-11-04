// Applies the saved appearance before first paint (Settings > Appearance). "system" follows the OS.
(()=>{try{const t=localStorage.getItem('rogueforge-theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}catch(e){}})();
