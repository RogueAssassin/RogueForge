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
  self.assertEqual(RELEASE,'0.8.5');self.assertEqual(self.app.VERSION,RELEASE);self.assertFalse(any(ROOT.glob('rogueforge_v*.py')))
  for n in ('rogueforge_ext.py','rogueforge_live.py','rogueforge_discovery.py','upgrade.sh'):self.assertFalse((ROOT/n).exists())
 def test_external_backup_dirs(self):
  self.assertIn('update-backups',self.app.EXCLUDED_DIRS);self.assertIn('rogueforge-update-backups',self.app.EXCLUDED_DIRS)
  p=self.root/'x'/'compose.yaml';p.parent.mkdir();p.write_text('services: {}\n');b=self.app._backup_file(p,'compose-backups');self.assertFalse(str(b).startswith(str(self.root)));self.assertTrue(b.is_file())
 def test_podman_stats_array_and_name_alias(self):
  old=self.app.engine_cli;self.app.engine_cli=lambda *a,**k:json.dumps([{'ID':'a'*64,'Name':'dozzle','CPUPerc':'1.25%','MemUsage':'42MiB / 1GiB'}])
  try:d=self.app.container_stats();self.assertEqual(d['a'*12]['cpu'],'1.25%');self.assertEqual(d['dozzle']['memory'],'42MiB / 1GiB')
  finally:self.app.engine_cli=old
 def test_compose_podman_command(self):
  p=self.root/'podman';p.mkdir();(p/'compose.yaml').write_text('services:\n  app:\n    image: test/app\n');self.app._discovery_cache['time']=0
  stack=next(x for x in self.app.discover_stacks() if x['relativePath']=='podman');old=self.app.runtime;self.app.runtime=lambda:{'engine':'podman','socket':'/tmp/podman.sock'}
  try:_,cmd,_=self.app.compose_command(stack['name'],['up','-d']);self.assertNotIn('--env-file',cmd);self.assertEqual(cmd[-2:],['up','-d'])
  finally:self.app.runtime=old
 def test_update_uses_direct_image_pull(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('pulled=engine_cli(["pull",m["image"]],900)',src);self.assertNotIn('run_compose(m["project"],["pull",m["service"]])',src)
 def test_active_project_discovery_precedence(self):
  src=(ROOT/'rogueforge.py').read_text();self.assertIn('Active Compose labels are authoritative',src);self.assertIn('labelled_projects',src)
 def test_release_files(self):
  for f in ('compose.yaml','.env.example','README.md'):self.assertIn(RELEASE,(ROOT/f).read_text())
  wf=(ROOT/'.github/workflows/container.yml').read_text();self.assertIn('python3 tools/apply_v085.py',wf);self.assertIn('type=raw,value=testing',wf);self.assertIn('Validate container build locally',wf)
 def test_ui_quality(self):
  controls=(ROOT/'static/container-controls.js').read_text();css=(ROOT/'static/operations.css').read_text();quality=(ROOT/'static/runtime-quality.js').read_text();loader=(ROOT/'static/branding/branding-switch.js').read_text()
  self.assertIn('const iconKey=c.image||c.service||c.name',controls);self.assertIn('rf-action-primary',controls);self.assertIn('object-position:center',css);self.assertIn('bestIdentity',quality);self.assertIn('/runtime-quality.js',loader)
 def test_testing_updater(self):
  u=(ROOT/'update.sh').read_text();self.assertIn('DEFAULT_TEST_BRANCH="v0.8.5-runtime-fixes"',u);self.assertIn('IMAGE_TAG=testing',u);self.assertIn('/tmp}/rogueforge/update-backups',u)
if __name__=='__main__':unittest.main()
