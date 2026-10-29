"""Build a reproducible Skill archive without local runtime/audit artifacts."""
import json
import hashlib
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "product-idea-research"
DIRECTORIES = {"agents", "assets", "evals", "references", "scripts", "security", "tests"}
ROOT_FILES = {"README.md", "SKILL.md", "manifest.json"}


def build():
    version = json.loads((SKILL / "manifest.json").read_text())["version"]
    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    paths = []
    # Only tracked or explicitly staged sources can enter a public archive.
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "skills/product-idea-research"], cwd=ROOT
    ).decode().split("\0")
    for name in filter(None, tracked):
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Not a regular source file: {name}")
        rel = path.relative_to(SKILL)
        if "__pycache__" in rel.parts or path.suffix == ".pyc" or path.name == ".DS_Store":
            continue
        if (len(rel.parts) == 1 and rel.name in ROOT_FILES) or rel.parts[0] in DIRECTORIES or rel.as_posix() == "reports/skill-ir.json":
            paths.append(path)
    if SKILL / "SKILL.md" not in paths or SKILL / "references/agent-compatibility.md" not in paths:
        raise ValueError("Stage the complete Skill sources before building")
    outputs = []
    for suffix, prefix in [("", "product-idea-research/"), ("-flat", "")]:
        output = output_dir / f"product-idea-research-v{version}{suffix}.zip"
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(paths):
                name = prefix + path.relative_to(SKILL).as_posix()
                entry = zipfile.ZipInfo(name, date_time=(2026, 10, 28, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes())
        print(f"Built {output.name}: {len(paths)} files")
        outputs.append(output)
    checksums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in outputs)
    (output_dir / "SHA256SUMS").write_text(checksums)
    return outputs


if __name__ == "__main__":
    build()
