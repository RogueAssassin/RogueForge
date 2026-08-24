import importlib.util
import hashlib
from http.client import HTTPConnection
import os
from pathlib import Path
import subprocess
import sys
import threading
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RogueForgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.stacks = Path(cls.temp.name)
        for name in ("immich", "media", "paperless"):
            folder = cls.stacks / name
            folder.mkdir()
            (folder / "compose.yaml").write_text("services:\n  app:\n    image: example/app\n", encoding="utf-8")
        os.environ["ROGUEFORGE_DEMO"] = "true"
        os.environ["ROGUEFORGE_STACKS_DIR"] = str(cls.stacks)
        spec = importlib.util.spec_from_file_location("rogueforge_test", ROOT / "rogueforge.py")
        cls.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_demo_runtime(self):
        self.assertEqual(self.app.runtime()["engine"], "demo")

    def test_container_normalization(self):
        items = self.app.containers()
        self.assertEqual(len(items), 4)
        self.assertEqual(sum(item["state"] == "running" for item in items), 3)
        self.assertTrue(all(len(item["id"]) == 12 for item in items))

    def test_stack_health_from_compose_labels(self):
        stacks = {item["name"]: item for item in self.app.discover_stacks()}
        self.assertEqual(stacks["immich"]["state"], "running")
        self.assertEqual(stacks["paperless"]["state"], "stopped")
        self.assertEqual(stacks["media"]["services"], 1)

    def test_stack_path_rejects_traversal(self):
        with self.assertRaises(ValueError):
            self.app.safe_stack("../escape")

    def test_demo_actions_are_non_mutating(self):
        result = self.app.run_stack_action("immich", "restart")
        self.assertTrue(result["ok"])
        self.assertIn("Demo mode", result["output"])

    def test_installer_supports_independent_custom_paths(self):
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        service = (ROOT / "systemd" / "rogueforge.service").read_text(encoding="utf-8")
        self.assertIn("--install-dir", installer)
        self.assertIn("--stacks-dir", installer)
        self.assertIn("--podman-user", installer)
        self.assertIn("--proxy-hostname", installer)
        self.assertIn("@INSTALL_DIR@", service)
        self.assertIn("@STACKS_DIR@", service)
        self.assertIn("@PROTECT_HOME@", service)

    def test_podman_compose_labels_are_recognized(self):
        original_demo = self.app.DEMO_MODE
        original_loader = self.app.engine_containers
        self.app.DEMO_MODE = False
        self.app.engine_containers = lambda: [{
            "Id": "a" * 64,
            "Names": ["podman-service"],
            "Image": "example/service:latest",
            "State": "running",
            "Status": "Up",
            "Labels": {"io.podman.compose.project": "podman-stack"},
            "Ports": [],
        }]
        try:
            item = self.app.containers()[0]
            self.assertEqual(item["project"], "podman-stack")
        finally:
            self.app.DEMO_MODE = original_demo
            self.app.engine_containers = original_loader

    def test_rootless_inventory_prefers_owner_cli(self):
        original_user = self.app.PODMAN_USER
        original_runtime = self.app.runtime
        original_command = self.app.podman_user_command
        self.app.PODMAN_USER = "administrator"
        self.app.runtime = lambda: {"engine": "podman"}
        self.app.podman_user_command = lambda args, timeout=30: '[{"Id":"abc","Names":["service"]}]'
        try:
            result = self.app.load_containers()
            self.assertEqual(result[0]["Names"], ["service"])
        finally:
            self.app.PODMAN_USER = original_user
            self.app.runtime = original_runtime
            self.app.podman_user_command = original_command

    def test_remote_inventory_uses_mounted_socket_cli(self):
        original_remote = self.app.PODMAN_REMOTE
        original_runtime = self.app.runtime
        original_command = self.app.podman_remote_command
        original_user = self.app.PODMAN_USER
        self.app.PODMAN_USER = ""
        self.app.PODMAN_REMOTE = True
        self.app.runtime = lambda: {"engine": "podman"}
        self.app.podman_remote_command = lambda args, timeout=30: '[{"Id":"def","Names":["rogueforge"]}]'
        try:
            result = self.app.load_containers()
            self.assertEqual(result[0]["Names"], ["rogueforge"])
        finally:
            self.app.PODMAN_REMOTE = original_remote
            self.app.runtime = original_runtime
            self.app.podman_remote_command = original_command
            self.app.PODMAN_USER = original_user

    def test_icon_directory_is_local_and_optional(self):
        original = self.app.ICONS_DIR
        with tempfile.TemporaryDirectory() as directory:
            self.app.ICONS_DIR = Path(directory)
            icon = self.app.ICONS_DIR / "uptime-kuma.svg"
            icon.write_text("<svg/>", encoding="utf-8")
            self.assertEqual(self.app.resolve_icon("uptime-kuma"), icon)
            self.assertIsNone(self.app.resolve_icon("missing-service"))
        self.app.ICONS_DIR = original

    def test_container_deployment_targets_media_net(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn('17810}:7810', compose)
        self.assertIn("name: media-net", compose)
        self.assertIn("container_name: rogueforge", compose)
        self.assertIn("ghcr.io/rogueassassin/rogueforge", compose)

    def test_password_hash_and_signed_session(self):
        salt = b"s" * 24
        password = "a-secure-test-password"
        iterations = 10_000
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        auth = {
            "username": "administrator",
            "salt": self.app.b64encode(salt),
            "passwordHash": self.app.b64encode(digest),
            "iterations": iterations,
            "sessionSecret": self.app.b64encode(b"k" * 48),
        }
        self.assertTrue(self.app.verify_password(password, auth))
        self.assertFalse(self.app.verify_password("wrong-password", auth))
        token, payload = self.app.make_session(auth)
        self.assertEqual(self.app.read_session(token, auth)["user"], "administrator")
        self.assertIsNone(self.app.read_session(token + "tampered", auth))
        self.assertTrue(payload["csrf"])

    def test_secure_icon_default_and_auth_provisioner(self):
        self.assertTrue(str(self.app.ICONS_DIR).replace("\\", "/").endswith("/opt/media-server/rogue-dashboard/app/static/icons"))
        provisioner = (ROOT / "setup-auth.py").read_text(encoding="utf-8")
        self.assertIn("pbkdf2_hmac", provisioner)
        self.assertNotIn("default_password", provisioner)

    def test_provisioner_never_stores_plaintext_password(self):
        with tempfile.TemporaryDirectory() as directory:
            auth_file = Path(directory) / "auth.json"
            process = subprocess.run([sys.executable, str(ROOT / "setup-auth.py"), "--username", "administrator", "--generate", "--auth-file", str(auth_file)], text=True, capture_output=True, timeout=20)
            self.assertEqual(process.returncode, 0, process.stderr)
            record = auth_file.read_text(encoding="utf-8")
            password = process.stdout.split("Generated password (shown once): ", 1)[1].strip()
            self.assertNotIn(password, record)
            self.assertIn("passwordHash", record)

    def test_ghcr_workflow_has_package_permissions(self):
        workflow = (ROOT / ".github" / "workflows" / "container.yml").read_text(encoding="utf-8")
        self.assertIn("packages: write", workflow)
        self.assertIn("ghcr.io/rogueassassin/rogueforge", workflow)
        self.assertIn("linux/amd64,linux/arm64", workflow)

    def test_privileged_http_actions_require_session_and_csrf(self):
        original_auth_file = self.app.AUTH_FILE
        salt = b"z" * 24
        password = "integration-test-password"
        iterations = 10_000
        record = {
            "username": "administrator",
            "salt": self.app.b64encode(salt),
            "passwordHash": self.app.b64encode(hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)),
            "iterations": iterations,
            "sessionSecret": self.app.b64encode(b"q" * 48),
        }
        auth_file = self.stacks.parent / "http-auth.json"
        auth_file.write_text(__import__("json").dumps(record), encoding="utf-8")
        self.app.AUTH_FILE = auth_file
        server = self.app.ThreadingHTTPServer(("127.0.0.1", 0), self.app.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            connection.request("POST", "/api/stacks/immich/restart", body=b"{}", headers={"content-type": "application/json"})
            response = connection.getresponse()
            self.assertEqual(response.status, 401)
            response.read()

            body = __import__("json").dumps({"username": "administrator", "password": password})
            connection.request("POST", "/api/auth/login", body=body, headers={"content-type": "application/json"})
            response = connection.getresponse()
            login = __import__("json").loads(response.read())
            cookie = response.getheader("set-cookie").split(";", 1)[0]
            self.assertEqual(response.status, 200)

            connection.request("POST", "/api/stacks/immich/restart", body=b"{}", headers={"content-type": "application/json", "cookie": cookie})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()

            connection.request("POST", "/api/stacks/immich/restart", body=b"{}", headers={"content-type": "application/json", "cookie": cookie, "x-csrf-token": login["csrf"]})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            response.read()
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            self.app.AUTH_FILE = original_auth_file


if __name__ == "__main__":
    unittest.main()
