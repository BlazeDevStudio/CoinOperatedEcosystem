import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_case_collisions.py")
sys.path.insert(0, HERE)
from check_case_collisions import find_collisions  # noqa: E402


class FindCollisions(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(find_collisions(["a/b.txt", "a/c.txt", "d/e"]), {})

    def test_directory_case_collision(self):
        got = find_collisions(["Pisonet/README.md", "pisonet/README.md"])
        self.assertEqual(got["pisonet"], ["Pisonet", "pisonet"])

    def test_nested_and_file_collision(self):
        got = find_collisions(["x/Readme.md", "x/README.md"])
        self.assertIn("x/readme.md", got)

    def test_same_spelling_is_not_a_collision(self):
        self.assertEqual(find_collisions(["Rental/a", "Rental/b"]), {})


class CliAgainstRealGit(unittest.TestCase):
    def _repo(self, files):
        d = tempfile.mkdtemp()
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        run = lambda *a: subprocess.run(a, cwd=d, env=env, check=True,
                                        capture_output=True)
        run("git", "init", "-q")
        for f in files:
            p = os.path.join(d, f)
            # Case-sensitive FS assumed here; skip otherwise.
            os.makedirs(os.path.dirname(p), exist_ok=True)
<<<<<<< HEAD
            with open(p, "w", encoding="utf-8") as fp:
                fp.write("x")
=======
            open(p, "w").write("x")
>>>>>>> feature/hardware-firmware-and-shared-contracts-20261111
        run("git", "add", "-A")
        run("git", "commit", "-qm", "t")
        return d

    def _cli(self, d):
        return subprocess.run([sys.executable, SCRIPT], cwd=d,
                              capture_output=True, text=True)

    def test_cli_flags_collision(self):
        d = self._repo(["Rental/a.md", "rental/a.md"])
        if len(os.listdir(d)) < 3:  # .git + only one spelling => case-insensitive FS
            self.skipTest("case-insensitive filesystem")
        r = self._cli(d)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("Rental", r.stdout)

    def test_cli_clean(self):
        d = self._repo(["Rental/a.md", "Pisonet/a.md"])
        self.assertEqual(self._cli(d).returncode, 0)

    def test_cli_git_error(self):
        d = tempfile.mkdtemp()
        r = subprocess.run([sys.executable, SCRIPT], cwd=d,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
