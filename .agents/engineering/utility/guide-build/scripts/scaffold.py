import argparse
import json
import os
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "template"
BUILDER_OWNED = ("build.py", "page.html", "open.sh", "README.md")


def template_bytes_for(name):
    data = (TEMPLATE / name).read_bytes()
    if name == "open.sh":
        data = data.replace(b"\r\n", b"\n")
    return data


def check(guide):
    drift = []
    for name in BUILDER_OWNED:
        target = guide / name
        template_bytes = template_bytes_for(name)
        if not target.exists() or target.read_bytes() != template_bytes:
            drift.append(name)
    if drift:
        for name in drift:
            print(f"drift: guide/{name}")
        raise SystemExit(1)


def write_builder_owned(guide):
    for name in BUILDER_OWNED:
        target = guide / name
        template_bytes = template_bytes_for(name)
        existed = target.exists()
        if existed and target.read_bytes() == template_bytes:
            continue
        target.write_bytes(template_bytes)
        if name == "open.sh":
            if os.name == "posix":
                target.chmod(0o755)
            else:
                print("scaffold: on Windows, mark it executable with: git add --chmod=+x guide/open.sh")
        print(f"{'replaced' if existed else 'created'} guide/{name}")


def write_repo_owned(guide):
    guide_json = guide / "guide.json"
    if not guide_json.exists():
        skeleton = {"title": "", "eyebrow": "", "repository": "", "output": ""}
        guide_json.write_text(json.dumps(skeleton, indent=2) + "\n", encoding="utf-8")
        print("created guide/guide.json — fill it in before the first build")

    annotations_json = guide / "annotations.json"
    if not annotations_json.exists():
        annotations_json.write_text("{}\n", encoding="utf-8")
        print("created guide/annotations.json")

    chapters = guide / "chapters"
    if not chapters.exists():
        chapters.mkdir(parents=True)
        print("created guide/chapters")


def scaffold(repo, check_only):
    if not repo.is_dir():
        raise SystemExit(f"scaffold: not a directory: {repo}")
    guide = repo / "guide"

    if check_only:
        check(guide)
        return

    guide.mkdir(parents=True, exist_ok=True)
    write_builder_owned(guide)
    write_repo_owned(guide)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    scaffold(Path(args.repo).resolve(), args.check)


if __name__ == "__main__":
    main()
