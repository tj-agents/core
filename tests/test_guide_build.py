"""Exercise the vendored guide builder template and its scaffold script."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE_BUILD = ROOT / ".agents/engineering/utility/guide-build"
SCAFFOLD = GUIDE_BUILD / "scripts/scaffold.py"
TEMPLATE = GUIDE_BUILD / "template"
BUILDER_OWNED = ("build.py", "page.html", "open.sh", "README.md")


def run(args, cwd):
    return subprocess.run(
        [sys.executable, *args], cwd=str(cwd), capture_output=True, text=True
    )


def git(args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)


def init_git_repo(root):
    git(["init"], root)
    git(["config", "user.name", "Guide Test"], root)
    git(["config", "user.email", "guide-test@example.com"], root)
    git(["config", "commit.gpgsign", "false"], root)


def write_fixture_sources(repo):
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "main.rs").write_text(
        "fn main() {\n"
        "    let x = 1;\n"
        '    println!("hello, {}", x);\n'
        "}\n"
        "\n"
        "fn helper() {\n"
        "    let y = 2;\n"
        "}\n",
        encoding="utf-8",
    )
    (repo / "Cargo.toml").write_text(
        "[package]\n"
        'name = "demo"\n'
        'version = "0.1.0"\n'
        "\n"
        "[dependencies]\n"
        'serde = "1"\n',
        encoding="utf-8",
    )


def commit_all(repo, message="fixture"):
    git(["add", "-A"], repo)
    git(["commit", "-m", message], repo)


def scaffold_repo(repo, extra=()):
    result = run([str(SCAFFOLD), "--repo", str(repo), *extra], cwd=repo)
    return result


def write_guide_json(repo, **overrides):
    config = {
        "title": "Demo Guide",
        "eyebrow": "Demo",
        "repository": "https://example.com/demo",
        "output": "target/guide/demo-guide.html",
    }
    config.update(overrides)
    (repo / "guide" / "guide.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    return config


def build(repo, extra=()):
    return run([str(repo / "guide" / "build.py"), *extra], cwd=repo)


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="guide-build-scaffold-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()

    def test_scaffold_creates_builder_and_repo_owned_files(self):
        result = scaffold_repo(self.repo)
        self.assertEqual(0, result.returncode, result.stderr)
        guide = self.repo / "guide"
        for name in BUILDER_OWNED:
            self.assertTrue((guide / name).exists(), name)
            self.assertEqual((guide / name).read_bytes(), (TEMPLATE / name).read_bytes())
        self.assertEqual(
            json.loads((guide / "guide.json").read_text(encoding="utf-8")),
            {"title": "", "eyebrow": "", "repository": "", "output": ""},
        )
        self.assertEqual(
            json.loads((guide / "annotations.json").read_text(encoding="utf-8")), {}
        )
        self.assertTrue((guide / "chapters").is_dir())

    def test_second_run_restores_edited_vendored_file_and_keeps_repo_owned(self):
        scaffold_repo(self.repo)
        guide = self.repo / "guide"
        (guide / "build.py").write_text("tampered", encoding="utf-8")
        write_guide_json(self.repo, title="Kept Title")

        result = scaffold_repo(self.repo)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("build.py", result.stdout)
        self.assertEqual((guide / "build.py").read_bytes(), (TEMPLATE / "build.py").read_bytes())
        self.assertEqual(
            json.loads((guide / "guide.json").read_text(encoding="utf-8"))["title"],
            "Kept Title",
        )

    def test_check_reports_drift_then_clean(self):
        scaffold_repo(self.repo)

        clean = scaffold_repo(self.repo, extra=("--check",))
        self.assertEqual(0, clean.returncode, clean.stderr)

        (self.repo / "guide" / "page.html").write_text("tampered", encoding="utf-8")
        dirty = scaffold_repo(self.repo, extra=("--check",))
        self.assertEqual(1, dirty.returncode)
        self.assertIn("page.html", dirty.stdout + dirty.stderr)

    def test_scaffolded_open_sh_has_lf_line_endings(self):
        scaffold_repo(self.repo)
        self.assertNotIn(b"\r", (self.repo / "guide" / "open.sh").read_bytes())

    def test_repo_must_be_existing_directory(self):
        missing = self.repo / "does-not-exist"
        result = run([str(SCAFFOLD), "--repo", str(missing)], cwd=self.repo)
        self.assertNotEqual(0, result.returncode)


class GuideFixture:
    def __init__(self, repo):
        self.repo = repo
        self.guide = repo / "guide"
        self.chapters = self.guide / "chapters"

    def write_chapter(self, name, text):
        self.chapters.mkdir(parents=True, exist_ok=True)
        (self.chapters / name).write_text(text, encoding="utf-8")

    def write_annotations(self, data):
        (self.guide / "annotations.json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )

    def build(self, extra=()):
        return build(self.repo, extra=extra)


def make_fixture(repo):
    init_git_repo(repo)
    write_fixture_sources(repo)
    scaffold_repo(repo)
    write_guide_json(repo)
    commit_all(repo)
    return GuideFixture(repo)


ANNOTATIONS = {
    "entry": {
        "owner": "Core Team",
        "marks": [
            {
                "id": "call-config",
                "match": "println!",
                "kind": "call",
                "target": "config",
                "label": "Reads configuration",
                "text": "Loads configuration values.",
                "focus": "[package]",
            },
            {
                "id": "note-x",
                "match": "let x",
                "kind": "data",
                "target": "readme-section",
                "label": "Local binding",
                "text": "Holds a local value.",
            },
        ],
    },
    "config": {
        "owner": "Core Team",
        "marks": [
            {
                "id": "owner-entry",
                "match": "[package]",
                "kind": "return",
                "target": "entry",
                "label": "Returns to main",
                "text": "Back to the entry point.",
            }
        ],
    },
}

CHAPTER_ONE = (
    "<!-- chapter: intro | Introduction -->\n"
    '<article class="chapter" id="intro">\n'
    '<div class="ch-head"><span class="eyebrow">Chapter @@N@@</span><h2>Introduction</h2></div>\n'
    '<div class="part">\n'
    "<p>This is the introduction. See chapter 2 for the configuration details.</p>\n"
    '@@CODE src/main.rs "fn helper()" block@@\n'
    '@@CODE src/main.rs "fn main()" +1 & "fn helper()" +1@@\n'
    "</div>\n"
    "</article>\n"
)

CHAPTER_TWO = (
    "<!-- chapter: setup | Configuration -->\n"
    '<article class="chapter" id="setup">\n'
    '<div class="ch-head"><span class="eyebrow">Chapter @@N@@</span><h2 id="readme-section">Configuration</h2></div>\n'
    '<div class="part">\n'
    '@@CODE Cargo.toml "[dependencies]" +2@@\n'
    '@@CODE Cargo.toml "[package]" .. "[dependencies]"@@\n'
    '@@CODE src/main.rs id=entry "fn main()" +2 & "println!" +1@@\n'
    '@@CODE Cargo.toml id=config "[package]" +3@@\n'
    "</div>\n"
    "</article>\n"
)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="guide-build-build-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        self.fixture = make_fixture(self.repo)

    def test_successful_build_renders_excerpts_and_substitutes_placeholders(self):
        self.fixture.write_chapter("01-intro.html", CHAPTER_ONE)
        self.fixture.write_chapter("02-setup.html", CHAPTER_TWO)
        self.fixture.write_annotations(ANNOTATIONS)

        result = self.fixture.build()
        self.assertEqual(0, result.returncode, result.stderr)

        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, capture_output=True, text=True, check=True
        ).stdout.strip()
        short_revision = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.repo, capture_output=True, text=True, check=True
        ).stdout.strip()

        output_path = self.repo / "target" / "guide" / "demo-guide.html"
        self.assertTrue(output_path.exists())
        page = output_path.read_text(encoding="utf-8")

        self.assertIn("<title>Demo Guide</title>", page)
        self.assertIn("<h1>Demo Guide</h1>", page)
        self.assertIn('<span class="eyebrow">Demo</span>', page)
        self.assertIn("<code>demo</code>", page)
        self.assertIn(short_revision, page)
        self.assertIn(
            f'<a href="https://example.com/demo/blob/{revision}/src/main.rs#L1">', page
        )
        self.assertIn(
            f'<a href="https://example.com/demo/blob/{revision}/Cargo.toml#L1">', page
        )
        self.assertIn("fn main()", page)
        self.assertIn("println!", page)
        self.assertIn('class="source-row elision"', page)
        self.assertIn("prism-rust.min.js", page)
        self.assertNotIn("prism-powershell.min.js", page)
        self.assertIn('<a href="#setup">chapter 2</a>', page)
        self.assertNotRegex(page, r"@@[A-Z_]+[^@]*@@")

    def test_print_output_prints_configured_path_and_builds_nothing(self):
        self.fixture.write_chapter("01-intro.html", CHAPTER_ONE)
        self.fixture.write_chapter("02-setup.html", CHAPTER_TWO)
        self.fixture.write_annotations(ANNOTATIONS)

        result = self.fixture.build(extra=("--print-output",))
        self.assertEqual(0, result.returncode, result.stderr)
        expected = str(self.repo / "target" / "guide" / "demo-guide.html")
        self.assertEqual(expected, result.stdout.strip())
        self.assertFalse((self.repo / "target").exists())

    def test_missing_excerpt_anchor_fails(self):
        self.fixture.write_chapter(
            "01-intro.html",
            "<!-- chapter: intro | Introduction -->\n"
            '<article class="chapter" id="intro">\n'
            '@@CODE src/main.rs "fn missing()" block@@\n'
            "</article>\n",
        )
        self.fixture.write_annotations({})

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("anchor not found", result.stderr)

    def test_guide_json_missing_key_fails(self):
        config = {"title": "T", "eyebrow": "E", "repository": "https://example.com/demo"}
        (self.fixture.guide / "guide.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        self.fixture.write_chapter("01-intro.html", CHAPTER_ONE)
        self.fixture.write_annotations({})

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("guide.json: missing key", result.stderr)

    def test_guide_json_unknown_key_fails(self):
        config = {
            "title": "T",
            "eyebrow": "E",
            "repository": "https://example.com/demo",
            "output": "target/guide/out.html",
            "extra": "nope",
        }
        (self.fixture.guide / "guide.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        self.fixture.write_chapter("01-intro.html", CHAPTER_ONE)
        self.fixture.write_annotations({})

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("guide.json: unknown key", result.stderr)

    def test_guide_json_empty_value_fails(self):
        config = {
            "title": "",
            "eyebrow": "E",
            "repository": "https://example.com/demo",
            "output": "target/guide/out.html",
        }
        (self.fixture.guide / "guide.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        self.fixture.write_chapter("01-intro.html", CHAPTER_ONE)
        self.fixture.write_annotations({})

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("guide.json: empty value", result.stderr)

    def test_id_excerpt_without_annotations_entry_fails(self):
        self.fixture.write_chapter(
            "01-intro.html",
            "<!-- chapter: intro | Introduction -->\n"
            '<article class="chapter" id="intro">\n'
            '@@CODE src/main.rs id=entry "fn main()" block@@\n'
            "</article>\n",
        )
        self.fixture.write_annotations({})

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("missing annotations", result.stderr)

    def test_unused_annotation_entry_fails(self):
        self.fixture.write_chapter(
            "01-intro.html",
            "<!-- chapter: intro | Introduction -->\n"
            '<article class="chapter" id="intro">\n'
            '<p>No excerpts here.</p>\n'
            "</article>\n",
        )
        self.fixture.write_annotations(
            {"orphan": {"owner": "Nobody", "marks": []}}
        )

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unused annotations", result.stderr)

    def test_missing_href_target_fails(self):
        self.fixture.write_chapter(
            "01-intro.html",
            "<!-- chapter: intro | Introduction -->\n"
            '<article class="chapter" id="intro">\n'
            '<p><a href="#missing">broken link</a></p>\n'
            "</article>\n",
        )
        self.fixture.write_annotations({})

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("missing internal targets", result.stderr)

    def test_chapter_without_header_comment_fails(self):
        self.fixture.write_chapter(
            "01-intro.html",
            '<article class="chapter" id="intro"><p>No header comment.</p></article>\n',
        )
        self.fixture.write_annotations({})

        result = self.fixture.build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("missing <!-- chapter: id | title -->", result.stderr)


if __name__ == "__main__":
    unittest.main()
