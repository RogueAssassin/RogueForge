import importlib.util, json, os, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RELEASE=(ROOT/'VERSION').read_text().strip()
class RogueForgeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name);os.environ['ROGUEFORGE_DEMO']='true';os.environ['ROGUEFORGE_STACKS_DIR']=str(cls.root)
  spec=importlib.util.spec_from_file_location('rogueforge_test',ROOT/'rogueforge.py');cls.app=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.app)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_release_and_single_runtime(self):
  self.assertRegex(RELEASE,r'^\d+\.\d+\.\d+$')
  self.assertEqual(self.app.VERSION,RELEASE)
  self.assertFalse(any(ROOT.glob('rogueforge_v*.py')))
  for n in ('rogueforge_ext.py','rogueforge_live.py','rogueforge_discovery.py','upgrade.sh'):self.assertFalse((ROOT/n).exists())
 def test_configurable_roots(self):
  self.assertEqual(self.app.COMPOSE_ROOT,self.app.STACKS_DIR);self.assertEqual(self.app.ENV_ROOT,self.app.COMPOSE_ROOT)
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('ROGUEFORGE_MEDIA_ROOT',src);self.assertIn('ROGUEFORGE_COMPOSE_ROOT',src);self.assertIn('ROGUEFORGE_ENV_ROOT',src);self.assertIn('def stack_env_path',src)
 def test_external_backup_dirs(self):
  self.assertIn('update-backups',self.app.EXCLUDED_DIRS);self.assertIn('rogueforge-update-backups',self.app.EXCLUDED_DIRS)
  p=self.root/'x'/'compose.yaml';p.parent.mkdir();p.write_text('services: {}\n');b=self.app._backup_file(p,'compose-backups');self.assertFalse(str(b).startswith(str(self.root)));self.assertTrue(b.is_file())
 def test_podman_stats_array_and_name_alias(self):
  old=self.app.engine_cli;self.app.engine_cli=lambda *a,**k:json.dumps([{'ID':'a'*64,'Name':'dozzle','CPUPerc':'1.25%','MemUsage':'42MiB / 1GiB'}])
  try:d=self.app.container_stats();self.assertEqual(d['a'*12]['cpu'],'1.25%');self.assertEqual(d['dozzle']['memory'],'42MiB / 1GiB')
  finally:self.app.engine_cli=old
 def test_update_uses_verified_podman_replacement(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('pulled=engine_cli(["pull",m["image"]],900)',src);self.assertIn('engine_cli(["rename",m["id"],preserved],60)',src);self.assertIn('Update verification failed',src);self.assertIn('engine_cli(["rename",preserved,old_name],60)',src)
 def test_inventory_snapshot_performance(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('def containers(inventory=None,registry=None):',src);self.assertIn('N+1 remote Podman calls',src)
 def test_shared_inventory_cache(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('ROGUEFORGE_INVENTORY_CACHE',src);self.assertIn('def _load_containers_uncached():',src);self.assertIn('def load_containers(force=False):',src);self.assertIn('def invalidate_inventory():',src)
  self.assertNotIn('def discover_stacks():\n    reg=_build_registry(force=True)',src)
 def test_media_server_stack_lifecycle(self):
  src=(ROOT/'rogueforge.py').read_text()
  self.assertIn('elif action=="stop":out=run_compose(stack,["down"])',src);self.assertIn('elif action=="restart":out=run_compose(stack,["down"])+"\\n"+run_compose(stack,["up","-d"])',src)
  self.assertIn('out=run_compose(name,["pull"])',src);self.assertIn('run_compose(name,["down"])',src);self.assertIn('run_compose(name,["up","-d"])',src)
 def test_http_disconnect_and_head_support(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('def do_HEAD(self):',src);self.assertIn('except (BrokenPipeError,ConnectionResetError)',src)
 def test_dashboard_snapshot_contract(self):
  backend=(ROOT/'rogueforge.py').read_text();frontend=(ROOT/'static/app.js').read_text()
  self.assertIn('/api/dashboard',backend);self.assertIn('function requestDashboard(force=false)',frontend);self.assertIn('const snapshot = await requestDashboard(force)',frontend)
  self.assertIn('DASHBOARD_CACHE_KEY',frontend);self.assertIn('hydrateDashboardSnapshot()',frontend);self.assertIn('sessionStorage.setItem',frontend)
  self.assertIn('if(!document.hidden) load({ quiet: true })',frontend);self.assertIn('visibilitychange',frontend)
  controls=(ROOT/'static/container-controls.js').read_text();self.assertIn('setTimeout(refreshContainerStats,1200)',controls);self.assertIn('setInterval(refreshContainerStats,15000)',controls)
 def test_media_server_compose_contract(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('PODMAN_COMPOSE_WARNING_LOGS',src);self.assertIn('stack_env_path(stack)',src)
  update=(ROOT/'update.sh').read_text();installer=(ROOT/'install.sh').read_text()
  self.assertIn('podman compose --env-file',update);self.assertNotIn('--pull never',update);self.assertNotIn('--pull never',installer)
 def test_active_project_discovery_precedence(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('Active Compose labels are authoritative',src);self.assertIn('labelled_projects',src)
 def test_release_files(self):
  for f in ('compose.yaml','.env.example','README.md'):self.assertIn(RELEASE,(ROOT/f).read_text())
  wf=(ROOT/'.github/workflows/container.yml').read_text();self.assertIn('Validate release and frontend consistency',wf);self.assertNotIn('python3 tools/prepare_runtime.py',wf);self.assertNotIn('tools/apply_v0',wf);self.assertIn('branches: [main, testing]',wf);self.assertNotIn('v0.8.7-testing',wf);self.assertIn('type=raw,value=testing',wf);self.assertNotIn('branch-${{ steps.version.outputs.safe_branch }}',wf)
  tools_py=list((ROOT/'tools').glob('*.py'));self.assertEqual(tools_py,[])
 def test_ui_quality(self):
  controls=(ROOT/'static/container-controls.js').read_text();css=(ROOT/'static/operations.css').read_text();operations=(ROOT/'static/operations.js').read_text();loader=(ROOT/'static/branding/branding-switch.js').read_text()
  self.assertIn('const iconKey=c.image||c.service||c.name',controls);self.assertIn('rf-action-primary',controls);self.assertIn('object-position:center',css);self.assertIn('function bestIdentity(key)',operations);self.assertNotIn('runtime-quality.js',loader);app=(ROOT/'static/app.js').read_text();self.assertIn('data-rf-config=',app);self.assertIn('data-rf-config-tab="compose"',app);self.assertIn('data-rf-config-tab="env"',app);self.assertNotIn('data-edit-stack="${attr(stack.name)}">Compose</button><button class="small-button" data-rf-env=',app)
 def test_static_assets_are_never_stale(self):
  src=(ROOT/'rogueforge.py').read_text();html=(ROOT/'static/index.html').read_text();css=(ROOT/'static/styles.css').read_text();app=(ROOT/'static/app.js').read_text()
  self.assertIn('cache-control","no-store, max-age=0"',src)
  self.assertNotIn('rf-app-footer',html);self.assertNotIn('rfFooterVersion',app)
  self.assertIn('Quick Actions final alignment fix',css)
  self.assertIn('display:grid!important',css);self.assertIn('text-align:center!important',css)
 def test_production_candidate_theme_preserves_branding(self):
  html=(ROOT/'static/index.html').read_text();app=(ROOT/'static/app.js').read_text();css=(ROOT/'static/styles.css').read_text()
  self.assertIn('/branding/rogueforge.svg',html);self.assertIn('rf-brand-crop',html)
  self.assertIn('rf-summary-icon',app);self.assertIn('rf-quick-icon',app);self.assertNotIn('rf-app-footer',html)
  self.assertIn('RogueForge 0.9 production-candidate visual system',css)
 def test_resource_relationships_and_cache(self):
  src=(ROOT/'rogueforge.py').read_text();app=(ROOT/'static/app.js').read_text();env=(ROOT/'.env.example').read_text()
  self.assertIn('ROGUEFORGE_RESOURCE_CACHE',src);self.assertIn('def _container_resource_snapshot()',src);self.assertIn('"containerCount"',src);self.assertIn('"containers":used',src)
  self.assertIn('?refresh=1',app);self.assertIn('resource-users',app);self.assertIn('invalidate_resource_cache()',src);self.assertIn('ROGUEFORGE_RESOURCE_CACHE=15',env)
 def test_read_only_runtime_resource_inventory(self):
  src=(ROOT/'rogueforge.py').read_text();html=(ROOT/'static/index.html').read_text();app=(ROOT/'static/app.js').read_text()
  for route in ('/api/images','/api/volumes','/api/networks'):self.assertIn(route,src)
  for view in ('images','volumes','networks'):self.assertIn(f'id="view-{view}"',html);self.assertIn(f'data-view="{view}"',html)
  self.assertIn('async function loadResource(kind',app);self.assertIn('function renderImages()',app);self.assertIn('function renderVolumes()',app);self.assertIn('function renderNetworks()',app)
  self.assertNotIn('/api/images/prune',src);self.assertNotIn('/api/volumes/prune',src);self.assertNotIn('/api/networks/prune',src)
 def test_frontend_optional_dom_nodes_are_safe(self):
  app=(ROOT/'static/app.js').read_text()
  self.assertIn('const setText =',app);self.assertIn('const setHtml =',app)
  for selector in ('#stackCount','#containerCount','#engineRuntime','#engineInitial','#engineVersion','#apiVersion'):
   self.assertNotIn(f'$("'+selector+'").textContent',app)
  self.assertIn('setText("#engineName", "Connection error")',app)
 def test_no_version_named_frontend_assets(self):
  names=[p.name for p in (ROOT/'static').iterdir() if p.is_file()]
  self.assertFalse(any(n.startswith('v0') for n in names))
  html=(ROOT/'static/index.html').read_text();self.assertNotIn('/v080',html)
 def test_testing_updater_and_roots(self):
  u=(ROOT/'update.sh').read_text();compose=(ROOT/'compose.yaml').read_text();env=(ROOT/'.env.example').read_text();installer=(ROOT/'install.sh').read_text()
  self.assertIn('DEFAULT_TEST_BRANCH="testing"',u);self.assertIn('IMAGE_TAG=testing',u);self.assertIn('REF="$BRANCH"; CHANNEL=testing',u);self.assertIn('/tmp}/rogueforge/update-backups',u)
  for key in ('ROGUEFORGE_MEDIA_ROOT','ROGUEFORGE_COMPOSE_ROOT','ROGUEFORGE_ENV_ROOT'):
   self.assertIn(key,compose);self.assertIn(key,env);self.assertIn(key,u);self.assertIn(key,installer)
  self.assertIn('ROGUEFORGE_INVENTORY_CACHE=2',env);self.assertIn(f'VERSION={RELEASE}',installer)
 def test_updater_does_not_self_overwrite_mid_run(self):
  u=(ROOT/'update.sh').read_text()
  first=u.index('install -m 0644 "$BACKUP/compose.download"')
  health=u.index('RogueForge $CHANNEL update complete.')
  refresh=u.index('install -m 0755 "$BACKUP/update.download" "$INSTALL_DIR/update.sh"')
  self.assertGreater(refresh,health);self.assertGreater(refresh,first)
  self.assertIn('bash -n update.sh',(ROOT/'.github/workflows/container.yml').read_text())
 def test_operation_timeout_and_progress_metadata(self):
  src=(ROOT/'rogueforge.py').read_text();ops=(ROOT/'static/operations.js').read_text();env=(ROOT/'.env.example').read_text();compose=(ROOT/'compose.yaml').read_text()
  self.assertIn('ROGUEFORGE_OPERATION_TIMEOUT',src);self.assertIn('threading.Timer(timeout,expire)',src);self.assertIn('status="timed_out"',src);self.assertIn('"stepCount"',src);self.assertIn('"currentStep"',src);self.assertIn('"failureReason"',src)
  self.assertIn('option value="timed_out"',ops);self.assertIn('Step ${Number(o.stepIndex||0)}/${Number(o.stepCount)}',ops)
  self.assertIn('ROGUEFORGE_OPERATION_TIMEOUT=900',env);self.assertIn('ROGUEFORGE_OPERATION_TIMEOUT:',compose)
 def test_server_backed_operations_closeout(self):
  src=(ROOT/'rogueforge.py').read_text();ops=(ROOT/'static/operations.js').read_text();app=(ROOT/'static/app.js').read_text()
  self.assertIn('ROGUEFORGE_OPERATIONS_FILE',src);self.assertIn('def start_operation(',src);self.assertIn('def cancel_operation(',src);self.assertIn('def _op_compose(',src);self.assertIn('subprocess.Popen(cmd',src);self.assertIn('/api/operations',src)
  self.assertIn("nativeFetch('/api/operations'",ops);self.assertIn('waitOperation',ops);self.assertIn('data-rf-cancel-op',ops);self.assertNotIn('localStorage.getItem(HISTORY_KEY)',ops)
  self.assertIn('async function refreshRuntimeInventory()',app);self.assertIn('await refreshRuntimeInventory()',app)
  self.assertIn('composePath',src);self.assertIn('directory',src);self.assertIn('Pin operations to the exact Compose path',src)
 def test_current_release_baseline(self):
  self.assertEqual((ROOT/'VERSION').read_text().strip(),'0.9.3')
  src=(ROOT/'rogueforge.py').read_text();road=(ROOT/'MILESTONES.md').read_text()
  self.assertIn('ROGUEFORGE_OPERATIONS_FILE',src);self.assertIn('def _load_containers_uncached()',src);self.assertIn('/api/dashboard',src)
  self.assertIn('## 0.9.3 — Frontend consolidation and security hardening',road)
 def test_transactional_stack_editor_writes(self):
  src=(ROOT/'rogueforge.py').read_text()
  self.assertIn('def _atomic_write(path,content):',src);self.assertIn('os.fsync(f.fileno())',src);self.assertIn('os.replace(tmp,path)',src)
  self.assertIn('def _transactional_stack_save(name,kind,content):',src);self.assertIn('validate_stack(name)',src);self.assertIn('rogueforge-restore-',src)
  self.assertIn('def save_stack_compose(name,content):return _transactional_stack_save(name,"compose",content)',src)
  self.assertIn('def save_stack_env(name,content):return _transactional_stack_save(name,"env",content)',src)
  self.assertNotIn('backup=_backup_file(p,"compose-backups");p.write_text(content,encoding="utf-8")',src)
 def test_stack_update_verification_and_rollback_foundation(self):
  src=(ROOT/'rogueforge.py').read_text()
  self.assertIn('def _stack_running_snapshot(name):',src);self.assertIn('def _verify_stack_running(name,before,timeout=45):',src)
  self.assertIn('Update safety check failed: stack has no running containers to preserve',src)
  self.assertIn('rollbackAttempted',src);self.assertIn('def _restore_stack_images(before):',src);self.assertIn('engine_cli(["tag",image_id,image_ref],60)',src)
  self.assertIn('str(c.get("state","")).lower()!="running"',src);self.assertNotIn('["config","--format","json"]',src)
  self.assertIn("Rollback {'succeeded' if rollback_ok else 'failed'}",src)
 def test_v092_dashboard_coalescing_and_swr(self):
  src=(ROOT/'rogueforge.py').read_text();app=(ROOT/'static/app.js').read_text();env=(ROOT/'.env.example').read_text();compose=(ROOT/'compose.yaml').read_text()
  self.assertIn('DASHBOARD_CACHE_SECONDS',src);self.assertIn('DASHBOARD_STALE_SECONDS',src);self.assertIn('def dashboard_snapshot(force=False):',src)
  self.assertIn('threading.Thread(target=_dashboard_refresh_background,daemon=True).start()',src);self.assertIn('invalidate_dashboard_cache()',src)
  self.assertIn('record_timing("dashboardBuild"',src);self.assertIn('record_timing("containerInventory"',src);self.assertIn('record_timing("containerStats"',src)
  self.assertIn('let dashboardRequest=null;',app);self.assertIn('function requestDashboard(force=false)',app);self.assertIn('?refresh=1',app);self.assertIn('await load({quiet:true,force:true})',app)
  self.assertIn('ROGUEFORGE_DASHBOARD_CACHE=3',env);self.assertIn('ROGUEFORGE_DASHBOARD_STALE=30',env);self.assertIn('ROGUEFORGE_DASHBOARD_CACHE:',compose)
 def test_v093_asset_graph_security_and_release_hygiene(self):
  root=(ROOT/'static/index.html').read_text();app=(ROOT/'static/app.js').read_text();brand=(ROOT/'static/branding/branding-switch.js').read_text();ops=(ROOT/'static/operations.js').read_text();src=(ROOT/'rogueforge.py').read_text()
  self.assertFalse((ROOT/'static/runtime-quality.js').exists())
  self.assertEqual(root.count('src="/operations.js"'),1);self.assertEqual(root.count('href="/operations.css"'),1)
  self.assertNotIn("script.src='/operations.js'",app);self.assertNotIn('/operations.js',brand);self.assertIn('function bestIdentity(key)',ops);self.assertIn("row.querySelector('.rf-action-secondary')",(ROOT/'static/live-ops.js').read_text())
  for header in ('x-frame-options','referrer-policy','permissions-policy','cross-origin-opener-policy'):self.assertIn(header,src)
  self.assertIn('h.send_security_headers();h.end_headers()',src)
  for path in ('static/app.js','static/container-controls.js','static/operations.js','static/live-ops.js','static/branding/branding-switch.js'):
   self.assertNotRegex((ROOT/path).read_text(),r'v0\.[0-9]')
  self.assertNotIn('container-row-v0',(ROOT/'static/container-controls.js').read_text());self.assertNotIn('container-head-v0',(ROOT/'static/container-controls.css').read_text());self.assertNotIn('container-actions-v0',(ROOT/'static/live-ops.js').read_text())

if __name__=='__main__':unittest.main()
