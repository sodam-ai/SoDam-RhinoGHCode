"""Execute emitted Rhino 7 Python bodies in the installed IronPython runtime.

The point and Rhino.Geometry objects are test doubles. No Rhino or Grasshopper
process is started, and no native component result is inferred from this test.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from detect_rhino_environment import gather_install
from offline_node import BOUNDS_IRONPYTHON_BODY, IRONPYTHON_BODY

HOST = r"""using System;
using System.IO;
using IronPython.Hosting;

class Program {
  static int Main(string[] args) {
    try {
      var engine = Python.CreateEngine();
      foreach (string path in args) {
        var scope = engine.CreateScope();
        engine.Execute(File.ReadAllText(path), scope);
      }
      Console.WriteLine("IronPython 2.7 emitted bodies executed and asserted");
      return 0;
    } catch (Exception error) {
      Console.Error.WriteLine(error);
      return 1;
    }
  }
}"""

SETUP = """import math
import sys
import imp

assert sys.version_info[0:2] == (2, 7), 'Rhino 7 IronPython 2.7 is required'

class Point(object):
    def __init__(self, x, y, z):
        self.X, self.Y, self.Z = float(x), float(y), float(z)
    @property
    def IsValid(self):
        return not any(math.isnan(v) or math.isinf(v) for v in (self.X, self.Y, self.Z))
    def DistanceTo(self, other):
        return math.sqrt((self.X-other.X)**2 + (self.Y-other.Y)**2 + (self.Z-other.Z)**2)
    def __add__(self, other):
        return Point(self.X+other.X, self.Y+other.Y, self.Z+other.Z)
    def __sub__(self, other):
        return Point(self.X-other.X, self.Y-other.Y, self.Z-other.Z)
    def __mul__(self, factor):
        return Point(self.X*factor, self.Y*factor, self.Z*factor)

rhino = imp.new_module('Rhino')
geometry = imp.new_module('Rhino.Geometry')
geometry.Point3d = Point
rhino.Geometry = geometry
sys.modules['Rhino'] = rhino
sys.modules['Rhino.Geometry'] = geometry
"""

POLYLINE_CASES = """
P = [Point(0, 0, 0), Point(2, 0, 0), Point(2, 2, 0)]
N = 4
""" + IRONPYTHON_BODY + """
assert [(p.X, p.Y, p.Z) for p in Pts] == [(0.,0.,0.),(1.,0.,0.),(2.,0.,0.),(2.,1.,0.),(2.,2.,0.)]
P = None
N = 4
""" + IRONPYTHON_BODY + """
assert Pts == []
P = [Point(0, 0, 0), Point(0, 0, 0)]
N = 2
""" + IRONPYTHON_BODY + """
assert Pts == []
P = [Point(0, 0, 0), Point(2, 0, 0), Point(2, 0, 0), Point(2, 4, 0)]
N = 3
""" + IRONPYTHON_BODY + """
assert [(p.X, p.Y, p.Z) for p in Pts] == [(0.,0.,0.),(2.,0.,0.),(2.,2.,0.),(2.,4.,0.)]
P = [Point(0, 0, 0), Point(float('nan'), 0, 0)]
N = 2
""" + IRONPYTHON_BODY + """
assert Pts == []
"""

BOUNDS_CASES = """
P = [Point(-1, 8, 2), Point(4, -2, 6), Point(0, 1, -5)]
""" + BOUNDS_IRONPYTHON_BODY + """
assert (Min.X, Min.Y, Min.Z) == (-1., -2., -5.)
assert (Max.X, Max.Y, Max.Z) == (4., 8., 6.)
P = []
""" + BOUNDS_IRONPYTHON_BODY + """
assert Min is None and Max is None
P = [Point(1, 2, 3), Point(float('nan'), 0, 0)]
""" + BOUNDS_IRONPYTHON_BODY + """
assert Min is None and Max is None
"""


def main() -> int:
    if sys.platform != "win32":
        print(json.dumps({"status": "fail", "error": "Windows Rhino 7 installation required"}))
        return 1
    install = gather_install("7")
    if install is None:
        print(json.dumps({"status": "fail", "error": "Rhino 7 installation not found"}))
        return 1
    runtime = Path(install["install_dir"]) / "Plug-ins" / "IronPython"
    names = ("IronPython.dll", "IronPython.Modules.dll", "Microsoft.Dynamic.dll",
             "Microsoft.Scripting.dll", "Microsoft.Scripting.Metadata.dll")
    missing = [name for name in names if not (runtime / name).is_file()]
    compiler = Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")
    if missing or not compiler.is_file():
        print(json.dumps({"status": "fail", "error": "Missing IronPython DLLs or C# compiler",
                          "missing": missing}))
        return 1
    with tempfile.TemporaryDirectory(prefix="rhino7-ironpython-") as temp_name:
        temp = Path(temp_name)
        for name in names:
            shutil.copy2(runtime / name, temp / name)
        (temp / "Host.cs").write_text(HOST, encoding="utf-8")
        (temp / "Polyline.py").write_text(SETUP + POLYLINE_CASES, encoding="utf-8")
        (temp / "Bounds.py").write_text(SETUP + BOUNDS_CASES, encoding="utf-8")
        compiled = subprocess.run(
            [str(compiler), "/nologo", "/target:exe", "/out:" + str(temp / "Host.exe"),
             "/r:" + str(temp / "IronPython.dll"),
             "/r:" + str(temp / "Microsoft.Scripting.dll"), str(temp / "Host.cs")],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        if compiled.returncode:
            print(json.dumps({"status": "fail", "phase": "compile",
                              "error": (compiled.stderr or compiled.stdout)[-1000:]}))
            return 1
        run = subprocess.run([str(temp / "Host.exe"), str(temp / "Polyline.py"),
                              str(temp / "Bounds.py")], cwd=temp,
                             capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        if run.returncode:
            print(json.dumps({"status": "fail", "phase": "execute",
                              "error": (run.stderr or run.stdout)[-1000:]}))
            return 1
    print(json.dumps({"status": "pass", "scope": "installed_rhino7_ironpython_with_point_stubs",
                      "operations": ["divide_polyline", "bounds_points"],
                      "native_grasshopper_execution": "not_verified"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
