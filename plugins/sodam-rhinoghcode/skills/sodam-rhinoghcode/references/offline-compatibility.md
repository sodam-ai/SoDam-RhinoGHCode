# Independent execution scope

The goal is useful node behavior without Rhino license activation. The independent path must produce a real result, not only syntax-checked code. This repository retains the original Grasshopper code-generation workflow and adds a separate evaluator inside the same project directory.

| Capability | Independent status | Evidence or boundary |
| --- | --- | --- |
| Rhino 7 target and IronPython/C# selection | Implemented, file-based | `detect_rhino_environment.py` reads installation files; no Rhino process starts. |
| Rhino 7 RhinoCommon member lookup | Implemented when local XML exists | `lookup_rhinocommon_docs.py --rhino-major 7`; XML lookup does not execute methods. |
| Rhino 7 component code and port instructions | Implemented as text output | Four fixed emitted point nodes and the documented Brep Tree body passed in a detached Rhino 7 Grasshopper document; arbitrary new code remains unverified. |
| License-free polyline division from a point list | Implemented and behavior-tested | `offline_node.py run` returns actual N + 1 3D points. Only open polyline point lists are supported. |
| License-free axis-aligned bounds of a point list | Implemented and behavior-tested | `offline_node.py run` returns minimum and maximum 3D corners. It does not create a Rhino `BoundingBox` object. |
| Matching Rhino 7 C# and GhPython bodies for both operations | Emitted, stub-tested, and native-tested for fixed cases | `test_offline_node.py` uses point stubs; `references/rhino7-native-probe-result-2026-09-27.json` records actual Rhino 7 Grasshopper outputs for the four emitted bodies. |
| Real Rhino 7 C# API signature check | Passed for both bundled C# bodies plus fixed trimmed Brep and Tree patterns on the current machine | `verify_rhino7_csharp_api.py` compiles against installed `RhinoCommon.dll`, `Grasshopper.dll`, and `GH_IO.dll` but never loads or executes the assembly. The Brep/Tree patterns are compile fixtures, not independently executed operations or arbitrary Codex answers. This does not verify component port wiring or native node behavior. |
| Installed Rhino 7 IronPython execution | Passed for both bundled GhPython bodies on the current machine | `verify_rhino7_ironpython.py` uses the installed IronPython 2.7 assemblies with point stubs; it does not load actual RhinoCommon geometry or run Grasshopper. |
| Arbitrary Curve/NURBS/Brep/Mesh/SubD RhinoCommon operations | Not implemented independently | The current evaluator has no corresponding geometry engine or semantics for them. |
| Grasshopper data trees, UI state, native node execution | Not implemented independently | The documented Brep Tree body passed a native detached-document check; independent execution and visible-canvas UI behavior remain outside the offline evaluator. |
| Rhino 8 runtime preservation | Source retained; execution unverified here | Rhino 8 is not installed on this machine. |

## Contract of the first supported operation

`divide_polyline` accepts `schema_version: 1`, an ordered `points` list of finite `[x,y,z]` coordinates, and `segment_count` from 1 to 10000. It returns N + 1 points at equal **arc lengths along the polyline**, including both endpoints. Zero-length edges inside an otherwise valid polyline are accepted. A fully degenerate polyline, nonfinite coordinates, unknown fields, unsupported operations, and oversized input are rejected explicitly.

The emitted Grasshopper scripts expect input `P` as a Point3d **List**, input `N` as an Integer **Item**, and output `Pts`. Set these ports in the Rhino 7 component UI. The independent runner takes JSON coordinates. Stub tests compare the emitted algorithms with its output; the fixed emitted bodies also passed the native probe.

`bounds_points` accepts `schema_version: 1` and one to 100000 finite `[x,y,z]` coordinates. It returns coordinate-wise `min` and `max` corners; one point produces identical corners. Empty lists, nonfinite coordinates, unknown fields, and oversized input are rejected. The emitted Rhino 7 scripts use Point3d **List** input `P` and Point3d outputs `Min` and `Max`; an empty input leaves both unset. These are axis-aligned bounds, with no document tolerance or Brep semantics. Results are exact min/max of the input floating-point coordinates, with no geometric approximation tolerance.

Commands from the repository root:

```powershell
python -B scripts/offline_node.py run offline-polyline-sample.json
python -B scripts/offline_node.py run offline-bounds-sample.json
python -B scripts/offline_node.py emit --language csharp
python -B scripts/offline_node.py emit --language ironpython
python -B scripts/offline_node.py emit --operation bounds_points --language csharp
python -B scripts/offline_node.py emit --operation bounds_points --language ironpython
python -B scripts/test_offline_node.py
```

Do not represent this first operation as full Grasshopper/RhinoCommon compatibility. Each additional operation needs an explicit input/output contract, independent result tests, and a separate record of any native-runtime result.
