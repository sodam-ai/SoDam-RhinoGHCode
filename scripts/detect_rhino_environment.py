from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if sys.platform != "win32":
    print(json.dumps({"error": "This detector currently supports Windows only."}, ensure_ascii=False))
    raise SystemExit(1)

import winreg

RUNTIME_KEYS = {
    "python3_runtime": "McNeel.Python39.Runtime.dll",
    "grasshopper": "Plug-ins/Grasshopper/Grasshopper.dll",
    "ghpython_component": "Plug-ins/Grasshopper/Components/GhPython.gha",
    "roslyn_bridge": "Rhino.Runtime.Code.Languages.Roslyn.dll",
    "csharp_compiler": "Microsoft.CodeAnalysis.CSharp.dll",
}

IRONPYTHON_PATHS = (
    "Plug-ins/IronPython/IronPython.dll",  # Rhino 7
    "System/IronPython.dll",  # Rhino 8
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--rhino-major", type=int, choices=(7, 8), help="Select the target Rhino version explicitly.")
    return parser.parse_args()


def read_reg_values(root: int, subkey: str) -> dict[str, Any] | None:
    try:
        with winreg.OpenKey(root, subkey) as key:
            values: dict[str, Any] = {}
            index = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, index)
                except OSError:
                    break
                values[name] = value
                index += 1
            return values
    except FileNotFoundError:
        return None


def file_version(path: Path) -> str | None:
    if not path.exists():
        return None
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"[System.Diagnostics.FileVersionInfo]::GetVersionInfo('{str(path).replace(chr(39), chr(39) * 2)}').FileVersion",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    version = result.stdout.strip() if result.returncode == 0 else ""
    return version or None


def detect_python_runtime_name(install_dir: Path) -> str | None:
    system_dir = install_dir / "System"
    for dll in system_dir.glob("McNeel.Python*.Runtime.dll"):
        match = re.search(r"Python(\d+)", dll.name)
        if not match:
            continue
        digits = match.group(1)
        if len(digits) == 2:
            return f"Python {digits[0]}.{digits[1]}"
        if len(digits) == 3:
            return f"Python {digits[0]}.{digits[1:]}"
        return f"Python {digits}"
    return None


def gather_install(major: str) -> dict[str, Any] | None:
    subkey = fr"SOFTWARE\McNeel\Rhinoceros\{major}.0\Install"
    values = read_reg_values(winreg.HKEY_LOCAL_MACHINE, subkey) or read_reg_values(winreg.HKEY_CURRENT_USER, subkey)
    if not values:
        return None

    install_dir_raw = values.get("InstallDir") or values.get("InstallPath")
    install_dir = Path(install_dir_raw).expanduser() if install_dir_raw else None
    exe_path_raw = values.get("ExePath")
    exe_path = Path(exe_path_raw) if exe_path_raw else (install_dir / "System" / "Rhino.exe" if install_dir else None)

    if not install_dir or not install_dir.exists() or not exe_path or not exe_path.exists():
        return None

    item: dict[str, Any] = {
        "rhino_major": int(major),
        "install_dir": str(install_dir),
        "rhino_exe": str(exe_path),
        "rhino_version": values.get("Version") or file_version(exe_path),
        "build_date": values.get("BuildDate"),
        "grasshopper_version": None,
        "python": {},
        "csharp": {},
    }

    if install_dir:
        grasshopper_path = install_dir / RUNTIME_KEYS["grasshopper"]
        ghpython_path = install_dir / RUNTIME_KEYS["ghpython_component"]
        roslyn_bridge_path = install_dir / "System" / RUNTIME_KEYS["roslyn_bridge"]
        csharp_compiler_path = install_dir / "System" / RUNTIME_KEYS["csharp_compiler"]
        python3_path = install_dir / "System" / RUNTIME_KEYS["python3_runtime"]
        ironpython_paths = [install_dir / rel for rel in IRONPYTHON_PATHS]
        ironpython_path = next((path for path in ironpython_paths if path.exists()), None)

        item["grasshopper_assembly_detected"] = grasshopper_path.exists()
        item["grasshopper_version"] = file_version(grasshopper_path)
        item["python"] = {
            "python3_runtime_detected": python3_path.exists(),
            "python3_runtime_name": detect_python_runtime_name(install_dir),
            "ironpython_detected": ironpython_path is not None,
            "ironpython_path": str(ironpython_path) if ironpython_path else None,
            "ghpython_component_detected": ghpython_path.exists(),
        }
        item["csharp"] = {
            "roslyn_bridge_detected": roslyn_bridge_path.exists(),
            "roslyn_bridge_version": file_version(roslyn_bridge_path),
            "compiler_detected": csharp_compiler_path.exists(),
            "compiler_version": file_version(csharp_compiler_path),
            "recommended_compatibility": "C# 9.0" if int(major) >= 8 else "Legacy Grasshopper C# script compatibility",
        }

    return item


def preferred_python(selected: dict[str, Any] | None) -> str | None:
    if selected is None:
        return None
    python = selected["python"]
    if selected["rhino_major"] >= 8 and python.get("python3_runtime_detected"):
        return python.get("python3_runtime_name") or "Python 3"
    if python.get("ironpython_detected"):
        return "IronPython 2.7"
    return None


def build_payload(installs: list[dict[str, Any]], requested_major: int | None = None) -> dict[str, Any]:
    selected = (
        next((item for item in installs if item["rhino_major"] == requested_major), None)
        if requested_major
        else max(installs, key=lambda item: item["rhino_major"], default=None)
    )
    error = None
    if requested_major and selected is None:
        error = f"Rhino {requested_major} was requested but was not detected."
    elif selected is None:
        error = "No supported Rhino installation was detected. Select a target version explicitly before generating node code."
    return {
        "detected": bool(installs),
        "error": error,
        "selected": selected,
        "installs": installs,
        "guidance": {
            "preferred_rhino": selected["rhino_major"] if selected else None,
            "preferred_python": preferred_python(selected),
            "preferred_csharp_compatibility": (
                selected["csharp"].get("recommended_compatibility")
                if selected
                else None
            ),
        },
    }


def main() -> int:
    args = parse_args()
    installs = []
    for major in ["8", "7"]:
        item = gather_install(major)
        if item:
            installs.append(item)
    payload = build_payload(installs, args.rhino_major)

    if args.pretty:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 1 if payload["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
