"""Reproduce ExactSplit checks using Python's standard library and pinned Fe."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import urllib.request

from generate_tests import prepare
from oracle import ROOT

VERSION = "26.5.0"
ASSETS = {
    "win32": ("fe_windows_amd64.exe", 61416960,
              "d86ca3c6fdadeb8335f7033e3a68fdb7d2aab4eafd22c1e23bec047d2a8b2674"),
    "linux": ("fe_linux_amd64", 54195184,
              "3732fbe8a6e9d2ea3925d02d0e3a1478bc1e01d742c2be75d3ea7300c46c45f0"),
}


def compiler(supplied: str | None, download: bool) -> Path:
    if platform.machine().lower() not in ("amd64", "x86_64"):
        raise ValueError("This runner supports x86-64 Windows and Linux only")
    if sys.platform not in ASSETS:
        raise ValueError("This runner supports Windows and Linux only")
    name, size, digest = ASSETS[sys.platform]
    target = Path(supplied).resolve() if supplied else ROOT / ".tools" / name
    if not target.is_file():
        if not download or supplied:
            raise FileNotFoundError("Supply --fe PATH or explicitly use --download-compiler")
        url = f"https://github.com/argotorg/fe/releases/download/v{VERSION}/{name}"
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(size + 1)
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("Official compiler download size/hash mismatch")
        target.parent.mkdir(parents=True, exist_ok=True)
        # The destination is project-local; the executable is never redistributed.
        target.write_bytes(data)
        if sys.platform == "linux":
            target.chmod(0o755)
    if target.stat().st_size != size or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise ValueError("Compiler differs from the pinned official release")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fe", help="path to the verified official Fe 26.5.0 executable")
    parser.add_argument("--download-compiler", action="store_true",
                        help="download the free official executable into .tools if absent")
    args = parser.parse_args()
    artifacts = ROOT / ".artifacts"
    artifacts.mkdir(exist_ok=True)
    report = dict(schema=1, started_utc=datetime.now(timezone.utc).isoformat(),
                  platform=sys.platform, python=platform.python_version(), steps=[], passed=False)
    fe = None

    def clean(text: str) -> str:
        paths = [(ROOT, "<project>")]
        if fe is not None:
            paths.append((fe, "<fe>"))
        for path, label in paths:
            text = text.replace(str(path), label).replace(path.as_posix(), label)
        return text

    def step(name, arguments, expected=0, diagnostic=None, test_count=None):
        completed = subprocess.run([str(fe), "--color", "never", *map(str, arguments)],
                                   cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", timeout=600, check=False)
        output = clean(completed.stdout)
        (artifacts / f"{name}.log").write_text(output, encoding="utf-8", newline="\n")
        record = dict(name=name, arguments=clean(" ".join(map(str, arguments))),
                      exit_code=completed.returncode, expected_exit=expected)
        report["steps"].append(record)
        if completed.returncode != expected:
            raise RuntimeError(f"{name}: unexpected exit; see .artifacts/{name}.log")
        if diagnostic and not re.search(diagnostic, output):
            raise RuntimeError(f"{name}: expected diagnostic missing")
        if test_count is not None:
            match = re.search(r"test result: ok[.] (\d+) passed; 0 failed", output)
            if not match or int(match.group(1)) != test_count:
                raise RuntimeError(f"{name}: wrong runtime test count")
            record["runtime_tests_passed"] = test_count
        print(f"PASS {name}")

    try:
        fe = compiler(args.fe, args.download_compiler)
        report["compiler_sha256"] = hashlib.sha256(fe.read_bytes()).hexdigest()
        step("version", ["--version"], diagnostic=r"fe 26[.]5[.]0")
        step("core-check", ["check", "."])
        step("core-tests", ["test", "--jobs", "1", "."], test_count=17)
        count = prepare(artifacts / "oracle-tests")
        step("oracle-tests", ["test", "--jobs", "1", ".artifacts/oracle-tests"], test_count=count)
        # Compiler checks are paired: a positive control must first compile.
        checks = json.loads((ROOT / "fixtures/compile-checks.json").read_text(encoding="utf-8"))
        for case in checks:
            if not re.fullmatch(r"[a-z0-9-]+", case["name"]):
                raise ValueError("Invalid compiler-check name")
            for kind, expected in [("positive", 0), ("negative", 1)]:
                fixture = (ROOT / "fixtures" / case[kind]).resolve()
                if not fixture.is_relative_to((ROOT / "fixtures").resolve()):
                    raise ValueError("Fixture path leaves the fixtures directory")
                ingot = artifacts / "compile-checks" / case["name"] / kind
                (ingot / "src").mkdir(parents=True, exist_ok=True)
                relative = Path(os.path.relpath(ROOT, ingot)).as_posix()
                manifest = ('[ingot]\nname = "compile_probe"\nversion = "0.1.0"\n\n'
                            f'[dependencies]\nexactsplit = {{ path = "{relative}" }}\n')
                (ingot / "fe.toml").write_text(manifest, encoding="utf-8", newline="\n")
                (ingot / "src/lib.fe").write_bytes(fixture.read_bytes())
                step(f'{case["name"]}-{kind}', ["check", ingot], expected=expected,
                     diagnostic=case["diagnostic_regex"] if kind == "negative" else None)
        report["passed"] = True
        report["fe_runtime_tests"] = 17 + count
        report["paired_compile_checks"] = len(checks)
        report["source_sha256"] = {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ["src", "scripts", "fixtures"]
            for p in sorted((ROOT / folder).rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        }
        print(f"PASS all checks: {17 + count} Fe runtime tests; {len(checks)} compiler pairs.")
        return 0
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
        report["error"] = clean(str(error))
        print(f"FAIL {report['error']}", file=sys.stderr)
        return 1
    finally:
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (artifacts / "verification.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
