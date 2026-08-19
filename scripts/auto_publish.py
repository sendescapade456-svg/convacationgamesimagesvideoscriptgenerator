#!/usr/bin/env python3
"""
Auto-publish changed HTML files to GitHub Pages via gh api.
Works around read-only .git mount by using Contents API.
Watches: cgames.html, index.html, glimmer.html (add more in WATCHED)
Run: python3 scripts/auto_publish.py [--once|--watch]
"""
import os, base64, subprocess, json, time, pathlib

REPO = "sendescapade456-svg/convacationgamesimagesvideoscriptgenerator"
BRANCH = "main"
WATCHED = ["cgames.html", "index.html", "glimmer.html"]

def gh_api(args, **kwargs):
    cmd = ["gh", "api"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r

def get_remote_sha(path):
    r = gh_api([f"repos/{REPO}/contents/{path}", "--jq", ".sha"])
    if r.returncode != 0:
        return None
    sha = r.stdout.strip()
    if not sha or "Not Found" in sha or "404" in sha or len(sha) < 10:
        return None
    return sha

def push_file(path):
    if not pathlib.Path(path).exists():
        print(f"SKIP {path} not found")
        return False
    content_b64 = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
    sha = get_remote_sha(path)
    # quick check: compare remote content to avoid no-op pushes
    if sha:
        r = gh_api([f"repos/{REPO}/contents/{path}", "--jq", ".content"])
        if r.returncode == 0 and r.stdout.strip():
            try:
                remote_b64 = "".join(r.stdout.strip().split())
                if remote_b64 == content_b64:
                    print(f"NO-OP {path} unchanged (sha {sha[:7]})")
                    return False
            except: pass
    print(f"PUSH {path} (remote sha {sha[:7] if sha else 'new'})")
    args = [
        "repos/{}/contents/{}".format(REPO, path),
        "--method", "PUT",
        "--field", f"message=auto-publish: update {path}",
        "--field", f"content={content_b64}",
        "--field", f"branch={BRANCH}",
    ]
    if sha:
        args.extend(["--field", f"sha={sha}"])
    r = gh_api(args)
    if r.returncode == 0:
        # gh api returns JSON; check for content.sha
        try:
            out = r.stdout
            # need to parse json
            data = json.loads(out) if out.strip().startswith("{") else {}
            new_sha = data.get("content", {}).get("sha", "")[:7]
            print(f"OK {path} -> {new_sha}")
        except:
            print(f"OK {path}")
        return True
    else:
        print(f"FAIL {path}: {r.stderr[:500]} {r.stdout[:500]}")
        return False

def push_all():
    changed = 0
    for f in WATCHED:
        if push_file(f):
            changed += 1
            time.sleep(1)  # avoid rate limit
    if changed == 0:
        print("No changes to publish")
    else:
        print(f"Published {changed} file(s) to https://sendescapade456-svg.github.io/convacationgamesimagesvideoscriptgenerator/")
    return changed

if __name__ == "__main__":
    import sys
    if "--watch" in sys.argv:
        print(f"Watching {WATCHED} with inotifywait (poll fallback every 30s)...")
        # try inotify, fallback to polling
        while True:
            try:
                subprocess.run(["inotifywait", "-e", "modify", "-q", "--timeout", "30"] + WATCHED, check=False)
            except FileNotFoundError:
                time.sleep(30)
            push_all()
    else:
        push_all()
