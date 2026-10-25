"""Package public source and the built frontend, never local configuration or data."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ENV_EXAMPLES = {".env.example", "deploy/.env.judging.example"}


def validate_public_release_name(name):
    """Accept only safe repository-relative paths and the two public env templates."""
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or path.as_posix() != name or ".." in path.parts
            or "\\" in name or ":" in name or any(ord(char) < 32 for char in name)):
        raise ValueError("Release contains an unexpected path.")
    if (any(part.lower().startswith(".env") for part in path.parts)
            and name not in PUBLIC_ENV_EXAMPLES):
        raise ValueError("Refusing to package private environment files.")
    if any(part.lower() in ("data", "judging-data", ".venv", "node_modules", ".git") for part in path.parts):
        raise ValueError("Refusing to package private runtime files.")
    if re.search(r"\.(?:sqlite3?|db|log)(?:$|[-.])", path.name.lower()):
        raise ValueError("Refusing to package runtime databases or logs.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise SystemExit("Build the frontend before packaging.")
    indexed = subprocess.check_output(["git","ls-files","--stage","-z"],cwd=ROOT).split(b"\0")
    sources = {}
    for entry in indexed:
        if not entry:
            continue
        metadata, name = entry.split(b"\t",1)
        mode, object_id, stage = metadata.decode().split()
        if stage != "0" or mode not in ("100644","100755"):
            raise SystemExit("Resolve conflicts and remove unsupported links before packaging.")
        name = name.decode()
        if (ROOT / name).is_file():
            sources[name] = object_id
    files = list(sources)
    files.extend(path.relative_to(ROOT).as_posix() for path in (ROOT / "frontend/dist").rglob("*") if path.is_file())
    if "THIRD_PARTY_NOTICES.txt" not in files:
        raise SystemExit("Generate and review THIRD_PARTY_NOTICES.txt before packaging a built frontend.")
    for name in files:
        path = Path(name)
        try:
            validate_public_release_name(name)
        except ValueError as exc:
            raise SystemExit(str(exc)) from None
        if any(ROOT.joinpath(*path.parts[:index]).is_symlink() for index in range(1, len(path.parts) + 1)):
            raise SystemExit("Refusing to package symbolic links.")
    # Read canonical staged blobs so Windows worktree line endings cannot alter
    # the release source or break the executable macOS shell launcher. Stage all
    # final source changes before packaging; CI checks out the committed index.
    object_ids = list(dict.fromkeys(sources.values()))
    batch = subprocess.check_output(["git","cat-file","--batch"],
        input="".join(object_id+"\n" for object_id in object_ids).encode(),cwd=ROOT)
    blobs, offset = {}, 0
    for object_id in object_ids:
        end = batch.index(b"\n",offset)
        returned_id, kind, size = batch[offset:end].decode().split()
        if returned_id != object_id or kind != "blob":
            raise SystemExit("A staged source file could not be read for packaging.")
        offset = end+1
        size = int(size)
        blobs[object_id] = batch[offset:offset+size]
        if len(blobs[object_id]) != size or batch[offset+size:offset+size+1] != b"\n":
            raise SystemExit("A staged source file was incomplete during packaging.")
        offset += size+1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output,"w",zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(files)):
            info = zipfile.ZipInfo("easy-street/" + Path(name).as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100755 if name.endswith(".command") else 0o100644) << 16
            archive.writestr(info,blobs[sources[name]] if name in sources else (ROOT / name).read_bytes())
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(f"{digest}  {args.output.name}\n",encoding="utf-8")
    print(f"Packaged {len(set(files))} public files: {args.output.name}")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
