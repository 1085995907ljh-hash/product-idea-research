"""Build a reproducible Skill archive without local runtime/audit artifacts."""
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "product-idea-research"
DIRECTORIES = {"agents", "assets", "evals", "references", "scripts", "security", "tests"}
ROOT_FILES = {"README.md", "SKILL.md", "manifest.json"}


def build():
    version = json.loads((SKILL / "manifest.json").read_text())["version"]
    output = ROOT / "dist" / f"product-idea-research-v{version}.zip"
    output.parent.mkdir(exist_ok=True)
    paths = []
    for path in SKILL.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(SKILL)
        if "__pycache__" in rel.parts or path.suffix == ".pyc" or path.name == ".DS_Store":
            continue
        if (len(rel.parts) == 1 and rel.name in ROOT_FILES) or rel.parts[0] in DIRECTORIES or rel.as_posix() == "reports/skill-ir.json":
            paths.append(path)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(paths):
            name = f"product-idea-research/{path.relative_to(SKILL).as_posix()}"
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 28, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    print(f"Built {output.name}: {len(paths)} files")
    return output


if __name__ == "__main__":
    build()
