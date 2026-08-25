import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
RELEASE=(ROOT/"VERSION").read_text().strip()

class RogueForgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.root=Path(cls.temp.name)
        os.environ["ROGUEFORGE_DEMO"]="true"; os.environ["ROGUEFORGE_STACKS_DIR"]=str(cls.root)
        spec=importlib.util.spec_from_file_location("rogueforge_test",ROOT/"rogueforge.py"); cls.app=importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.app)
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_version_and_single_runtime_layout(self):
        self.assertEqual(RELEASE,"0.8.4")
        self.assertEqual(self.app.VERSION,RELEASE)
        self.assertTrue((ROOT/"rogueforge.py").is_file())
        self.assertFalse(any(ROOT.glob("rogueforge_v*.py")))
        for name in ("rogueforge_ext.py","rogueforge_live.py","rogueforge_discovery.py","upgrade.sh"):
            self.assertFalse((ROOT/name).exists(),name)
        self.assertTrue((ROOT/"update.sh").is_file())

    def test_demo_runtime(self): self.assertEqual(self.app.runtime()["engine"],"demo")

    def test_recursive_discovery_and_nested_stack(self):
        nested=self.root/"apps"/"media"/"sonarr"; nested.mkdir(parents=True,exist_ok=True); (nested/"compose.yaml").write_text("services:\n  sonarr:\n    image: linuxserver/sonarr\n",encoding="utf-8")
        self.app._discovery_cache["time"]=0
        stack=next(x for x in self.app.discover_stacks() if x["relativePath"]=="apps/media/sonarr")
        self.assertEqual(stack["composeFile"],"compose.yaml")
        self.assertEqual(self.app.safe_stack(stack["name"]),nested.resolve())

    def test_update_backup_directories_are_excluded(self):
        self.assertIn("update-backups",self.app.EXCLUDED_DIRS)
        self.assertIn("rogueforge-update-backups",self.app.EXCLUDED_DIRS)
        nested=self.root/"data"/"update-backups"/"old"; nested.mkdir(parents=True,exist_ok=True); (nested/"compose.yaml").write_text("services:\n  old:\n    image: old/test\n",encoding="utf-8")
        self.app._discovery_cache["time"]=0
        self.assertFalse(any("update-backups" in x["relativePath"] for x in self.app.discover_stacks()))

    def test_compose_command_podman_does_not_use_env_file(self):
        nested=self.root/"podman-test"; nested.mkdir(exist_ok=True); (nested/"compose.yaml").write_text("services:\n  app:\n    image: test/app\n",encoding="utf-8"); (nested/".env").write_text("A=B\n",encoding="utf-8")
        self.app._discovery_cache["time"]=0; stack=next(x for x in self.app.discover_stacks() if x["relativePath"]=="podman-test")
        old_runtime=self.app.runtime; self.app.runtime=lambda:{"engine":"podman","socket":"/tmp/podman.sock"}
        try:
            _,cmd,_=self.app.compose_command(stack["name"],["pull"]); self.assertNotIn("--env-file",cmd); self.assertIn("-f",cmd); self.assertEqual(cmd[-1],"pull")
        finally:self.app.runtime=old_runtime

    def test_container_metadata_and_self_protection(self):
        old=self.app.load_containers
        self.app.load_containers=lambda:[{"Id":"a"*64,"Names":["rogueforge"],"Image":f"ghcr.io/rogueassassin/rogueforge:{RELEASE}","State":"running","Labels":{"io.podman.compose.project":"rogueforge","io.podman.compose.service":"rogueforge"},"Ports":[]}]
        try:
            item=self.app.containers()[0]; self.assertEqual(item["id"],"a"*12); self.assertTrue(item["selfProtected"]); self.assertEqual(item["service"],"rogueforge")
        finally:self.app.load_containers=old

    def test_release_files_are_consistent(self):
        compose=(ROOT/"compose.yaml").read_text(); env=(ROOT/".env.example").read_text(); container=(ROOT/"Containerfile").read_text(); workflow=(ROOT/".github/workflows/container.yml").read_text(); readme=(ROOT/"README.md").read_text()
        for content in (compose,env,readme): self.assertIn(RELEASE,content)
        self.assertNotIn('org.opencontainers.image.version="0.8.3"',container)
        self.assertIn('COPY rogueforge.py setup-auth.py VERSION ./',container)
        self.assertIn('CMD ["python3", "/opt/rogueforge/rogueforge.py"]',container)
        self.assertIn("VERSION=$(cat VERSION)",workflow)
        self.assertIn("type=raw,value=v${{ steps.version.outputs.version }}",workflow)
        self.assertIn("compact",workflow)
        self.assertIn("packages: write",workflow)

    def test_branding_is_clean_three_variant_set(self):
        branding=ROOT/"static"/"branding"; self.assertTrue((branding/"rogueforge.svg").is_file()); self.assertTrue((branding/"rogueforge-dark.svg").is_file()); self.assertTrue((branding/"rogueforge-light.svg").is_file())
        for obsolete in ("rogueforge-base.svg","rogueforge-logo.svg","rogueforge-wordmark-dark.svg","rogueforge-wordmark-light.svg","favicon.svg"):
            self.assertFalse((branding/obsolete).exists(),obsolete)
        html=(ROOT/"static/index.html").read_text(); self.assertIn('/branding/rogueforge.svg',html); self.assertNotIn('rogueforge-base.svg',html)

    def test_operations_and_icon_resolver_assets(self):
        js=(ROOT/"static/operations.js").read_text(); css=(ROOT/"static/operations.css").read_text(); loader=(ROOT/"static/branding/branding-switch.js").read_text()
        self.assertIn("nginx-proxy-manager",js); self.assertIn("cloudflared",js); self.assertIn("cloudflare",js)
        self.assertIn("cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons",js); self.assertIn("raw.githubusercontent.com/homarr-labs/dashboard-icons",js)
        self.assertIn("rogueforge-operation-history-v2",js); self.assertIn("rfOperationsDrawer",js); self.assertIn("rf-operations-drawer",css)
        self.assertIn("/operations.js",loader); self.assertIn("/operations.css",loader)
        self.assertFalse((ROOT/"static/v083.js").exists()); self.assertFalse((ROOT/"static/v083.css").exists())

    def test_update_script_uses_external_backups_and_health_check(self):
        update=(ROOT/"update.sh").read_text(); self.assertIn("data/auth.json",update); self.assertIn("rogueforge-update-backups",update); self.assertIn("LEGACY_BACKUPS",update); self.assertIn("/health",update); self.assertIn("latest|main|X.Y.Z",update)
        self.assertNotIn('BACKUP="$INSTALL_DIR/data/update-backups/',update)

if __name__=="__main__": unittest.main()
