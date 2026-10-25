"""Release safety checks use disposable Git repositories and fixture settings only."""
import hashlib
import stat
import subprocess
import sys
import zipfile

import pytest

from scripts import package_release, smoke_release, smoke_startup


@pytest.mark.parametrize("name",[
    ".env.example", "deploy/.env.judging.example", "README.md",
    "backend/provider.py", "frontend/dist/assets/index.js",
])
def test_public_release_paths_are_allowed(name):
    package_release.validate_public_release_name(name)


@pytest.mark.parametrize("name",[
    ".env", ".env.local", "deploy/.env", "deploy/.env.example",
    "nested/.env.judging.example", "deploy/.env.judging.example.bak", ".ENV.EXAMPLE",
    ".env.example/private.txt", "data/course.json", "judging-data/control.sqlite3",
    "nested/Data/upload.txt", ".git/config", ".venv/bin/python", "node_modules/index.js",
    "control.sqlite", "control.sqlite3-wal", "control.sqlite3-shm", "control.db-journal",
    "runtime.log", "runtime.log.1", "nested/RUNTIME.LOG.gz",
    "../README.md", "/README.md", "a/../README.md", "a//README.md", "./README.md",
    "a\\README.md", "C:/README.md", "file:stream", "",
])
def test_private_runtime_and_unsafe_paths_are_rejected(name):
    with pytest.raises(ValueError):
        package_release.validate_public_release_name(name)


def git(root,*args,input=None):
    return subprocess.check_output(["git",*args],cwd=root,input=input,stderr=subprocess.PIPE)


@pytest.fixture
def release_tree(tmp_path,monkeypatch):
    root=tmp_path/"source"
    root.mkdir()
    git(root,"init","-q")
    git(root,"config","core.autocrlf","false")
    for name,content in {
        ".env.example":"OPENAI_API_KEY=\nNEBIUS_API_KEY=\n",
        "deploy/.env.judging.example":"NEBIUS_API_KEY=\n",
        "README.md":"Canonical staged source.\n",
        "THIRD_PARTY_NOTICES.txt":"Fixture notices.\n",
        "Start Easy Street.command":"#!/bin/sh\nexit 0\n",
    }.items():
        path=root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content,encoding="utf-8",newline="\n")
    git(root,"add",".")
    dist=root/"frontend/dist"
    dist.mkdir(parents=True)
    (dist/"index.html").write_text("<title>Easy Street</title>",encoding="utf-8")
    monkeypatch.setattr(package_release,"ROOT",root)
    output=tmp_path/"release.zip"
    monkeypatch.setattr(sys,"argv",["package_release.py","--output",str(output)])
    return root,output


def test_release_keeps_exact_public_templates_and_canonical_staged_bytes(release_tree):
    root,output=release_tree
    (root/"README.md").write_bytes(b"Unstaged Windows source.\r\n")
    package_release.main()
    with zipfile.ZipFile(output) as archive:
        names=set(archive.namelist())
        assert names == {"easy-street/"+name for name in (
            ".env.example","deploy/.env.judging.example","README.md","THIRD_PARTY_NOTICES.txt",
            "Start Easy Street.command","frontend/dist/index.html")}
        assert archive.read("easy-street/README.md") == b"Canonical staged source.\n"
        assert archive.read("easy-street/deploy/.env.judging.example") == b"NEBIUS_API_KEY=\n"
        launcher=archive.getinfo("easy-street/Start Easy Street.command")
        assert stat.S_IMODE(launcher.external_attr >> 16) == 0o755
    assert output.with_suffix(".zip.sha256").read_text(encoding="utf-8") == (
        hashlib.sha256(output.read_bytes()).hexdigest()+"  release.zip\n")


@pytest.mark.parametrize("name",["deploy/.env.example","judging-data/session.json","runtime.sqlite3-wal"])
def test_packager_rejects_private_tracked_files_before_writing_archive(release_tree,name):
    root,output=release_tree
    private=root/name
    private.parent.mkdir(parents=True,exist_ok=True)
    private.write_text("private fixture only",encoding="utf-8")
    git(root,"add","-f",name)
    with pytest.raises(SystemExit,match="Refusing"):
        package_release.main()
    assert not output.exists()


def test_packager_rejects_indexed_symbolic_link_on_every_platform(release_tree):
    root,output=release_tree
    object_id=git(root,"hash-object","-w","--stdin",input=b"README.md").decode().strip()
    git(root,"update-index","--add","--cacheinfo",f"120000,{object_id},linked-readme")
    with pytest.raises(SystemExit,match="unsupported links"):
        package_release.main()
    assert not output.exists()


def test_packager_rejects_built_asset_symbolic_link(release_tree):
    root,output=release_tree
    try:
        (root/"frontend/dist/linked.txt").symlink_to(root/"README.md")
    except OSError:
        pytest.skip("Creating symbolic links requires privileges on this platform.")
    with pytest.raises(SystemExit,match="symbolic links"):
        package_release.main()
    assert not output.exists()


def test_smoke_environment_removes_both_providers_and_inherited_hosted_settings():
    original={"PATH":"fixture-path","OPENAI_API_KEY":"fixture-openai", "NEBIUS_API_KEY":"fixture-nebius",
        "nebius_base_url":"https://invalid.example", "OPENAI_MODEL":"fixture-model",
        "EASY_STREET_PROVIDER":"nebius", "EASY_STREET_DEMO_MODE":"judging",
        "EASY_STREET_DATA_DIR":"private-path", "EASY_STREET_BUDGET_USD":"100",
        "PYTHON_DOTENV_DISABLED":"0"}
    isolated=smoke_startup.isolated_environment(original)
    assert isolated == {"PATH":"fixture-path","OPENAI_API_KEY":"","NEBIUS_API_KEY":"",
        "EASY_STREET_BUDGET_USD":"0","PYTHON_DOTENV_DISABLED":"1","PYTHONUNBUFFERED":"1"}
    assert original["NEBIUS_API_KEY"] == "fixture-nebius"


def test_smoke_usage_check_rejects_a_key_on_the_nonselected_provider(monkeypatch):
    monkeypatch.setattr(smoke_startup,"api",lambda _: {"key_configured":False,"providers":[
        {"name":"openai","key_configured":False},{"name":"nebius","key_configured":True}]})
    with pytest.raises(RuntimeError,match="API key"):
        smoke_startup.verify_no_usage()


@pytest.mark.parametrize("name,mode",[
    ("easy-street/deploy/.env.example",0o100644),
    ("easy-street/judging-data/session.json",0o100644),
    ("easy-street/runtime.db-wal",0o100644),
    ("easy-street/README.md",0o120777),
])
def test_release_smoke_rejects_private_files_and_links_before_setup(tmp_path,monkeypatch,name,mode):
    output=tmp_path/"unsafe.zip"
    with zipfile.ZipFile(output,"w") as archive:
        info=zipfile.ZipInfo(name)
        info.create_system=3
        info.external_attr=mode << 16
        archive.writestr(info,b"fixture content")
    monkeypatch.setattr(sys,"argv",["smoke_release.py",str(output)])
    monkeypatch.setattr(smoke_release.subprocess,"run",lambda *a,**k:pytest.fail("Unsafe archive reached setup."))
    with pytest.raises(SystemExit,match="(Refusing|symbolic links)"):
        smoke_release.main()
