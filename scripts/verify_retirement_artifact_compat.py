"""Verify synthetic artifact action outputs without touching retirement resources."""

import io
import os
import time
import urllib.parse
import zipfile

from scripts.fly_shutdown import Http, ShutdownError, digest


def main():
    artifact_id = os.environ["TEST_ARTIFACT_ID"]
    expected = "sha256:" + os.environ["TEST_ARTIFACT_DIGEST"]
    run_id = os.environ["GITHUB_RUN_ID"]
    token = os.environ["GITHUB_TOKEN"]
    if not artifact_id.isdecimal() or not run_id.isdecimal() or len(expected) != 71:
        raise ValueError("Invalid synthetic artifact reference")
    if os.environ["GITHUB_REPOSITORY"] != "agammann/easy-street":
        raise ValueError("Unexpected repository")
    http = Http()
    endpoint = "https://api.github.com/repos/agammann/easy-street/actions/artifacts/" + artifact_id
    for attempt in range(3):
        try:
            metadata = http.json("GET", endpoint, token)
            break
        except ShutdownError as error:
            if getattr(error, "status", None) != 404 or attempt == 2:
                raise
            time.sleep(10)
    if (str(metadata.get("id")) != artifact_id or metadata.get("expired") is not False
            or metadata.get("name") != "synthetic-retirement-action-compat-" + run_id
            or str(metadata.get("workflow_run", {}).get("id")) != run_id
            or metadata.get("digest") != expected):
        raise ValueError("Synthetic artifact metadata did not match action outputs")
    status, headers, _ = http.raw("GET", endpoint + "/zip", token, redirect=True)
    location = headers.get("Location", headers.get("location", ""))
    parsed = urllib.parse.urlsplit(location)
    if (status != 302 or parsed.scheme != "https" or parsed.username or parsed.password
            or not parsed.hostname or not parsed.hostname.endswith((".blob.core.windows.net", ".actions.githubusercontent.com"))):
        raise ValueError("Unexpected artifact storage location")
    _, _, archived = http.raw("GET", location)  # Never forward the GitHub token to storage.
    if "sha256:" + digest(archived) != expected:
        raise ValueError("Synthetic artifact digest mismatch")
    with zipfile.ZipFile(io.BytesIO(archived)) as archive:
        if (sorted(archive.namelist()) != ["ledger.cms", "receipt.json"]
                or archive.read("ledger.cms") != b"synthetic ciphertext\n"
                or archive.read("receipt.json") != b'{"fixture":true}\n'):
            raise ValueError("Synthetic artifact contents did not match")
    print("Synthetic artifact metadata, digest and contents verified.")


if __name__ == "__main__":
    main()
