#!/usr/bin/env python3
"""폐쇄망(air-gap) 반입·설치 키트 — 표준 라이브러리만 사용.

인터넷이 되는 빌드 PC에서 번들을 만들고(bundle), 폐쇄망에서는 번들만으로 검증·설치·자체시험을 한다.

  python airgap/airgap.py bundle   [--images] [--with-tests] [--python 3.12] [--out dist]
      → dist/<이름>-airgap-<커밋>/ 와 같은 이름의 .tar.gz(+.sha256)
        wheelhouse/      의존성 wheel 전부(바이너리만, 대상 Python·플랫폼 고정)
        requirements.lock  해시 고정 목록(pip --require-hashes)
        source.tar       저장소 소스(git archive HEAD)
        images/*.tar     (선택) docker save 이미지 — 앱 이미지 + 외부 이미지
        sbom.cdx.json    CycloneDX 1.6 SBOM(wheel 메타데이터 기준)
        manifest.json, SHA256SUMS
  python airgap.py verify   <번들 폴더|tar.gz>          SHA256SUMS 대조(반입 직후)
  python airgap.py install  <번들 폴더> [--venv DIR] [--with-tests]
                                                      네트워크 없이 venv 설치(--no-index --require-hashes)
  python airgap.py selftest <번들 폴더>                설치 → 시험 → 기동 확인(네트워크 차단 상태에서 실행)
  python airgap.py egress-check [--env-file F] [--strict]
                                                      외부 주소 설정이 폐쇄망 내부를 가리키는지 검사
  python airgap.py preflight [--env-file F]            기동 전 점검: egress-check(엄격) + 필수 비밀값(빈 값·기본값·짧은 값 금지)
  python airgap.py images-from-compose <compose.yml ...>  compose 파일의 image: 목록(외부 이미지 반입 목록 작성용)

설정은 airgap/airgap.json 이다. 키트는 K-PVOS 도구체계(폐쇄망 반입 절차)와 같은 순서를 따른다:
라이선스 검토 → 체크섬 → 내부 미러 → SBOM → PoC 증빙 → 버전 고정.
"""
import argparse
import email.parser
import hashlib
import ipaddress
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KIT_VERSION = "1.0.0"
PLATFORMS = ["manylinux_2_28_x86_64", "manylinux_2_17_x86_64", "manylinux2014_x86_64", "linux_x86_64"]
INTERNAL_SUFFIX = (".internal", ".local", ".lan", ".corp", ".intra", ".localdomain", ".svc", ".cluster.local", ".home.arpa")


def load_config():
    return json.loads((HERE / "airgap.json").read_text(encoding="utf-8"))


def sh(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_rev():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "nogit"


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


# ---------------------------------------------------------------- bundle
def requirement_files(cfg, with_tests):
    req = [ROOT / r for r in cfg.get("requirements", [])]
    extras = list(cfg.get("extras", []))
    if with_tests:
        req += [ROOT / r for r in cfg.get("test_requirements", [])]
        extras += cfg.get("test_extras", [])
    return req, extras


def download(cfg, wheelhouse, py, with_tests):
    req, extras = requirement_files(cfg, with_tests)
    tmp = Path(tempfile.mkdtemp())
    reqs = tmp / "all.txt"
    lines = []
    for r in req:
        for ln in r.read_text(encoding="utf-8").splitlines():
            ln = ln.split("#", 1)[0].strip()
            if ln and not ln.startswith("-"):
                lines.append(ln)
    if extras or cfg.get("pyproject"):
        # pyproject 의존성(선택 extras 포함)을 직접 읽는다
        import tomllib
        pp = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        lines += pp.get("dependencies", [])
        for e in extras:
            lines += pp.get("optional-dependencies", {}).get(e, [])
    lines += cfg.get("extra_packages", [])
    excluded = {norm(x) for x in cfg.get("exclude_runtime", [])} if not with_tests else set()
    lines = [l for l in lines if norm(re.split(r"[<>=!~\[; ]", l, 1)[0]) not in excluded]
    reqs.write_text("\n".join(sorted(set(lines))) + "\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "pip", "download", "-r", reqs, "-d", wheelhouse, "--only-binary=:all:",
           "--python-version", py, "--implementation", "cp", "--disable-pip-version-check"]
    for p in cfg.get("platforms", PLATFORMS):
        cmd += ["--platform", p]
    sh(cmd)
    return lines


def wheel_meta(whl):
    with zipfile.ZipFile(whl) as z:
        name = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
        m = email.parser.Parser().parsestr(z.read(name).decode("utf-8", "replace"))
    expr = (m.get("License-Expression") or "").strip()
    if expr:
        return m["Name"], m["Version"], {"expression": expr}
    names = [c.split("::")[-1].strip() for c in m.get_all("Classifier", []) if c.startswith("License ::")]
    if not names and (m.get("License") or "").strip():
        names = [(m.get("License") or "").strip().splitlines()[0][:100]]
    lic = {"names": names} if names else None
    return m["Name"], m["Version"], lic


def write_lock(wheelhouse, out):
    by = {}
    for w in sorted(Path(wheelhouse).glob("*.whl")):
        name, ver, _ = wheel_meta(w)
        by.setdefault((norm(name), ver), []).append(sha256(w))
    lines = [f"# 자동 생성(airgap.py {KIT_VERSION}) — 수정 금지. pip install --no-index --require-hashes -r requirements.lock"]
    for (name, ver), hs in sorted(by.items()):
        lines.append(f"{name}=={ver} " + " ".join(f"--hash=sha256:{h}" for h in sorted(set(hs))))
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(by)


def write_sbom(cfg, wheelhouse, out, rev):
    comps = []
    for w in sorted(Path(wheelhouse).glob("*.whl")):
        name, ver, lic = wheel_meta(w)
        c = {"type": "library", "name": name, "version": ver, "purl": f"pkg:pypi/{norm(name)}@{ver}",
             "hashes": [{"alg": "SHA-256", "content": sha256(w)}], "properties": [{"name": "airgap:file", "value": w.name}]}
        if lic and "expression" in lic:
            c["licenses"] = [{"expression": lic["expression"]}]
        elif lic:
            c["licenses"] = [{"license": {"name": n}} for n in lic["names"]]
        comps.append(c)
    bom = {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
           "metadata": {"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "tools": {"components": [{"type": "application", "name": "airgap.py", "version": KIT_VERSION}]},
                        "component": {"type": "application", "name": cfg["name"], "version": rev}},
           "components": comps}
    Path(out).write_text(json.dumps(bom, ensure_ascii=False, indent=1), encoding="utf-8")
    return comps


def license_review(comps, cfg):
    deny = [d.lower() for d in cfg.get("license_deny", ["AGPL", "SSPL", "BUSL", "Elastic License", "Commons Clause"])]
    hits, unknown = [], []
    for c in comps:
        lic = json.dumps(c.get("licenses", []), ensure_ascii=False).lower()
        if not c.get("licenses"):
            unknown.append(f"{c['name']} {c['version']}")
        elif any(d in lic for d in deny):
            hits.append(f"{c['name']} {c['version']}: {lic}")
    return hits, unknown


def save_images(cfg, out_dir, rev):
    if not shutil.which("docker"):
        raise SystemExit("--images 에는 docker 가 필요하다")
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for im in cfg.get("images", []):
        tag = f"{im['name']}:{rev}"
        sh(["docker", "build", "-t", tag, "-t", f"{im['name']}:airgap", "-f", ROOT / im.get("dockerfile", "Dockerfile"), ROOT / im.get("context", ".")])
        saved.append(tag)
    for ext in cfg.get("external_images", []):
        sh(["docker", "pull", ext])
        saved.append(ext)
    for tag in saved:
        f = out_dir / (re.sub(r"[^A-Za-z0-9_.-]+", "_", tag) + ".tar")
        sh(["docker", "save", "-o", f, tag])
    return saved


def cmd_bundle(a):
    cfg = load_config()
    rev = git_rev()
    name = f"{cfg['name']}-airgap-{rev}"
    out = Path(a.out).resolve() / name
    if out.exists():
        shutil.rmtree(out)
    wh = out / "wheelhouse"
    wh.mkdir(parents=True)
    py = a.python or cfg.get("python", "3.12")
    download(cfg, wh, py, with_tests=False)
    if cfg.get("pyproject"):
        sh([sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", wh, "--disable-pip-version-check", ROOT])
    n = write_lock(wh, out / "requirements.lock")
    if a.with_tests:
        twh = out / "wheelhouse-test"
        twh.mkdir()
        download(cfg, twh, py, with_tests=True)
        for w in twh.glob("*.whl"):
            if not (wh / w.name).exists():
                shutil.move(str(w), wh / w.name)
            else:
                w.unlink()
        twh.rmdir()
        write_lock(wh, out / "requirements-test.lock")
    comps = write_sbom(cfg, wh, out / "sbom.cdx.json", rev)
    hits, unknown = license_review(comps, cfg)
    if (ROOT / ".git").exists():
        sh(["git", "-C", ROOT, "archive", "--format=tar", "-o", out / "source.tar", "HEAD"])
    else:
        with tarfile.open(out / "source.tar", "w") as t:
            t.add(ROOT, arcname=".", filter=lambda ti: None if "/dist" in ti.name or "/.git" in ti.name else ti)
    images = save_images(cfg, out / "images", rev) if a.images else []
    shutil.copy2(__file__, out / "airgap.py")
    shutil.copy2(HERE / "airgap.json", out / "airgap.json")
    for doc in ("AIRGAP.md",):
        if (HERE / doc).exists():
            shutil.copy2(HERE / doc, out / doc)
    manifest = dict(name=cfg["name"], revision=rev, kit=KIT_VERSION, created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    python=py, platforms=cfg.get("platforms", PLATFORMS), packages=n, with_tests=a.with_tests, images=images,
                    license_flags=hits, license_unknown=unknown, build_host_python=sys.version.split()[0])
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    write_sums(out)
    tgz = out.parent / f"{name}.tar.gz"
    with tarfile.open(tgz, "w:gz") as t:
        t.add(out, arcname=name)
    tgz.with_suffix(".gz.sha256").write_text(f"{sha256(tgz)}  {tgz.name}\n", encoding="utf-8")
    print(f"\n번들: {tgz}\nSHA-256: {sha256(tgz)}\n패키지 {n}개, 이미지 {len(images)}개")
    if hits:
        print("라이선스 검토 필요:\n  " + "\n  ".join(hits))
    if unknown:
        print("라이선스 미상(수동 확인):\n  " + "\n  ".join(unknown))
    return 0


def write_sums(out):
    lines = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            lines.append(f"{sha256(p)}  {p.relative_to(out).as_posix()}")
    (out / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- verify / install / selftest
def open_bundle(path):
    p = Path(path).resolve()
    if p.is_file() and p.name.endswith(".tar.gz"):
        side = Path(str(p) + ".sha256") if Path(str(p) + ".sha256").exists() else p.with_suffix(".gz.sha256")
        if side.exists() and side.read_text().split()[0] != sha256(p):
            raise SystemExit(f"번들 파일 해시 불일치: {p.name}")
        dest = Path(tempfile.mkdtemp(prefix="airgap-"))
        with tarfile.open(p) as t:
            t.extractall(dest, filter="data")
        p = next(dest.iterdir())
    return p


def cmd_verify(a):
    b = open_bundle(a.bundle)
    bad, missing = [], []
    listed = set()
    for ln in (b / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        h, rel = ln.split("  ", 1)
        listed.add(rel)
        f = b / rel
        if not f.exists():
            missing.append(rel)
        elif sha256(f) != h:
            bad.append(rel)
    extra = [p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file() and p.name != "SHA256SUMS" and p.relative_to(b).as_posix() not in listed]
    ok = not bad and not missing and not extra
    print(f"검증 {'통과' if ok else '실패'}: {len(listed)}개 파일, 변조 {len(bad)}, 누락 {len(missing)}, 목록 밖 파일 {len(extra)}")
    for x in bad + missing + extra:
        print("  ", x)
    return 0 if ok else 1


def venv_python(v):
    return Path(v) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def pick_interpreter(target):
    """번들 대상 Python 버전과 같은 인터프리터를 찾는다(python3.12 등). 없으면 현재 것으로 폴백(경고)."""
    for cand in (f"python{target}", f"python{target.split('.')[0]}"):
        exe = shutil.which(cand)
        if exe:
            v = subprocess.run([exe, "-c", "import sys;print('%d.%d'%sys.version_info[:2])"], capture_output=True, text=True).stdout.strip()
            if v == target:
                return exe
    cur = "%d.%d" % sys.version_info[:2]
    if cur != target:
        print(f"경고: 대상 Python {target} 인터프리터를 못 찾았다. 현재 {cur}로 진행하면 바이너리 wheel이 맞지 않을 수 있다 — 대상 PC에서는 {target}로 설치할 것.")
    return sys.executable


def install(b, venv, with_tests):
    if cmd_verify(argparse.Namespace(bundle=str(b))) != 0:
        raise SystemExit("번들 검증 실패 — 설치 중단")
    src = Path(venv).resolve().parent / "src"
    src.mkdir(parents=True, exist_ok=True)
    with tarfile.open(b / "source.tar") as t:
        t.extractall(src, filter="data")
    manifest = json.loads((b / "manifest.json").read_text(encoding="utf-8"))
    sh([pick_interpreter(manifest.get("python", "%d.%d" % sys.version_info[:2])), "-m", "venv", venv])
    py = venv_python(venv)
    lock = b / ("requirements-test.lock" if with_tests and (b / "requirements-test.lock").exists() else "requirements.lock")
    sh([py, "-m", "pip", "install", "--no-index", "--find-links", b / "wheelhouse", "--require-hashes", "--disable-pip-version-check", "-r", lock])
    cfg = json.loads((b / "airgap.json").read_text(encoding="utf-8"))
    if cfg.get("pyproject"):
        proj = norm(cfg.get("dist_name") or cfg["name"])
        wheels = [w for w in sorted((b / "wheelhouse").glob("*.whl")) if norm(w.name.split("-")[0]) == proj]
        if not wheels:
            raise SystemExit(f"프로젝트 wheel을 찾지 못함(이름 {proj}). airgap.json의 dist_name 확인")
        sh([py, "-m", "pip", "install", "--no-index", "--no-deps", "--disable-pip-version-check", wheels[-1]])
    print(f"설치 완료: venv={venv}, 소스={src}")
    return py, src, cfg


def cmd_install(a):
    b = open_bundle(a.bundle)
    install(b, a.venv, a.with_tests)
    return 0


def egress_blocked():
    try:
        urllib.request.urlopen("https://pypi.org/simple/", timeout=3)
        return False
    except Exception:
        return True


def cmd_selftest(a):
    b = open_bundle(a.bundle)
    if not egress_blocked():
        msg = "경고: 외부 네트워크가 열려 있다. 폐쇄망 검증이 되려면 차단된 환경(unshare -rn, docker --network none)에서 실행한다."
        if a.require_offline:
            raise SystemExit(msg)
        print(msg)
    work = Path(a.workdir or tempfile.mkdtemp(prefix="airgap-selftest-"))
    py, src, cfg = install(b, work / "venv", with_tests=True)
    env = {**os.environ, **cfg.get("selftest_env", {}), "PATH": f"{py.parent}{os.pathsep}{os.environ.get('PATH', '')}"}
    results = {}
    for t in cfg.get("tests", []):
        cwd = src / t.get("cwd", ".")
        r = subprocess.run([str(py) if x == "{python}" else x for x in t["cmd"]], cwd=cwd, env={**env, **t.get("env", {})})
        results[t["name"]] = r.returncode == 0
        print(f"[시험] {t['name']}: {'통과' if r.returncode == 0 else '실패'}")
    for s in cfg.get("smoke", []):
        cwd = src / s.get("cwd", ".")
        p = subprocess.Popen([str(py) if x == "{python}" else x for x in s["cmd"]], cwd=cwd, env={**env, **s.get("env", {})}, start_new_session=True)
        ok = False
        for _ in range(int(s.get("timeout", 30) * 4)):
            try:
                with urllib.request.urlopen(urllib.request.Request(s["url"]), timeout=1) as r:
                    ok = 200 <= r.status < 300
                    break
            except Exception:
                time.sleep(0.25)
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except Exception:
            p.terminate()
        p.wait(timeout=10)
        results[s["name"]] = ok
        print(f"[기동] {s['name']}: {'통과' if ok else '실패'} ({s['url']})")
    report = dict(bundle=b.name, at=datetime.now(timezone.utc).isoformat(timespec="seconds"), offline=egress_blocked(), results=results,
                  manifest=json.loads((b / "manifest.json").read_text(encoding="utf-8")))
    (work / "selftest-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"자체시험 보고서: {work / 'selftest-report.json'}")
    return 0 if results and all(results.values()) else 1


# ---------------------------------------------------------------- egress-check
URL_KEY = re.compile(r".*(_URL|_URI|_ENDPOINT|_BASE_URL|_HOST|_ISSUER|_JWKS_URL)$")


def host_allowed(host, allow):
    if not host:
        return True
    h = host.lower().strip("[]")
    if h in allow or any(h.endswith("." + a) for a in allow):
        return True
    if h in ("localhost",) or h.endswith(INTERNAL_SUFFIX) or "." not in h:
        return True  # 단일 레이블(서비스 이름) 또는 내부 접미사
    try:
        ip = ipaddress.ip_address(h)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def cmd_egress(a):
    cfg = load_config() if (HERE / "airgap.json").exists() else {}
    env = read_env(a.env_file)
    allow = {x.strip().lower() for x in (env.get("AIRGAP_ALLOWED_HOSTS", "") + "," + ",".join(cfg.get("allowed_hosts", []))).split(",") if x.strip()}
    keys = set(cfg.get("url_env", [])) | {k for k in env if URL_KEY.match(k)}
    bad = []
    for k in sorted(keys):
        v = env.get(k, "")
        if not v:
            continue
        u = urlparse(v if "://" in v else "//" + v)
        if not host_allowed(u.hostname, allow):
            bad.append((k, u.hostname))
    for k, h in bad:
        print(f"외부 주소: {k} → {h} (내부 주소·AIRGAP_ALLOWED_HOSTS 로 바꿀 것)")
    print(f"egress-check: {'통과' if not bad else f'{len(bad)}건 위반'} (검사 {len([k for k in keys if env.get(k)])}개 변수)")
    return 1 if bad and a.strict else 0


def read_env(env_file):
    env = dict(os.environ)
    if env_file:
        for ln in Path(env_file).read_text(encoding="utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def cmd_preflight(a):
    cfg = load_config()
    env = read_env(a.env_file)
    bad = []
    for spec in cfg.get("secret_env", []):
        k = spec["name"]
        v = env.get(k, "")
        if not v:
            bad.append(f"{k}: 비어 있음")
        elif v in spec.get("forbidden", []) or re.search(r"(change-?me|replace-with|example|dummy|secret$)", v, re.I):
            bad.append(f"{k}: 기본값·예시값 사용")
        elif len(v) < spec.get("min_length", 24):
            bad.append(f"{k}: {spec.get('min_length', 24)}자 미만")
    for b in bad:
        print("비밀값:", b)
    rc = cmd_egress(argparse.Namespace(env_file=a.env_file, strict=True))
    print(f"preflight: {'통과' if not bad and rc == 0 else '실패'}")
    return 0 if not bad and rc == 0 else 1


def cmd_images(a):
    seen = []
    for f in a.files:
        for m in re.finditer(r"^\s*image:\s*[\"']?([^\s\"'#]+)", Path(f).read_text(encoding="utf-8"), re.M):
            if m.group(1) not in seen:
                seen.append(m.group(1))
    for s in seen:
        print(s)
    floating = [s for s in seen if ":" not in s.split("/")[-1] or s.endswith(":latest")]
    if floating:
        print("# 태그 고정 필요(latest·무태그):", ", ".join(floating), file=sys.stderr)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="폐쇄망 반입·설치 키트")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("bundle"); p.add_argument("--out", default=str(ROOT / "dist")); p.add_argument("--python")
    p.add_argument("--images", action="store_true"); p.add_argument("--with-tests", action="store_true"); p.set_defaults(f=cmd_bundle)
    p = sub.add_parser("verify"); p.add_argument("bundle"); p.set_defaults(f=cmd_verify)
    p = sub.add_parser("install"); p.add_argument("bundle"); p.add_argument("--venv", default=".venv-airgap"); p.add_argument("--with-tests", action="store_true"); p.set_defaults(f=cmd_install)
    p = sub.add_parser("selftest"); p.add_argument("bundle"); p.add_argument("--workdir"); p.add_argument("--require-offline", action="store_true"); p.set_defaults(f=cmd_selftest)
    p = sub.add_parser("egress-check"); p.add_argument("--env-file"); p.add_argument("--strict", action="store_true"); p.set_defaults(f=cmd_egress)
    p = sub.add_parser("preflight"); p.add_argument("--env-file"); p.set_defaults(f=cmd_preflight)
    p = sub.add_parser("images-from-compose"); p.add_argument("files", nargs="+"); p.set_defaults(f=cmd_images)
    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
