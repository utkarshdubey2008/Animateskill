#!/usr/bin/env python3
import json
import mimetypes
import sys
import urllib.request
import uuid
from pathlib import Path


def upload_to_tmpfiles(filepath: str) -> str:
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")

    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    with open(path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        "https://tmpfiles.org/api/v1/upload",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))

    if res_data.get("status") == "success":
        url = res_data["data"]["url"]
        # Convert standard tmpfiles view URL into direct download URL by inserting /dl/
        dl_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        return dl_url
    else:
        raise RuntimeError(f"Upload failed: {res_data}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: upload_tmpfiles.py <file1> [file2...]")
        sys.exit(1)
    for p in sys.argv[1:]:
        url = upload_to_tmpfiles(p)
        print(f"{p} -> {url}")
