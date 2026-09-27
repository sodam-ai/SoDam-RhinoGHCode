# Official Rhino And Grasshopper Notes

Use these notes for version-sensitive behaviour. They are distilled from current McNeel developer documentation and local installation inspection.

## Official docs used

- Rhino.Python version comparison (Rhino 7 IronPython 2.7; Rhino 8 CPython 3.9):
  - https://developer.rhino3d.com/guides/rhinopython/what-is-rhinopython/
- Legacy GhPython guide:
  - https://developer.rhino3d.com/guides/rhinopython/ghpython-question-answer/

- Grasshopper Script Component overview:
  - https://developer.rhino3d.com/en/guides/scripting/scripting-component/
- Grasshopper Python scripting guide:
  - https://developer.rhino3d.com/guides/scripting/scripting-gh-python/
- Grasshopper C# scripting guide:
  - https://developer.rhino3d.com/guides/scripting/scripting-gh-csharp/
- Essential C# Scripting for Grasshopper:
  - https://developer.rhino3d.com/en/guides/grasshopper/csharp-essentials/1-grasshopper-csharp-component/
- Official sample repository:
  - https://github.com/mcneel/rhino-developer-samples
- RhinoCommon API docs:
  - https://mcneel.github.io/rhinocommon-api-docs/

## Facts from official docs

- Rhino 7's built-in Python is IronPython 2.7. GhPython can access RhinoCommon and rhinoscriptsyntax.
- The Rhino 8 unified Script component, Python 3 Script, and Python SDK-Mode are Rhino 8 features. Rhino 7 users must configure legacy component inputs and outputs in the Grasshopper UI.

- Rhino 8 has the unified Grasshopper Script component and dedicated C# / Python script workflows.
- The generic Script component can run multiple supported languages.
- Python 3 scripts in Rhino 8 can install packages via `pip`.
- C# scripts in Rhino 8 can install packages via `NuGet`.
- Python 3 scripting supports both Script-Mode and SDK-Mode.
- Script input parameters are optional by default; as of Rhino 8.14 there is a Required toggle on inputs.
- Rhino 8 Python scripting docs explicitly describe both Python 3 and IronPython 2 components.
- The Python editor status bar shows the Python language version.
- Grasshopper scripting docs explicitly describe parameter access and note that script outputs are object-typed.
- In C# script components, `Single Item` access can cause the script to execute once per incoming item instead of once for the whole collection.

## Local RhinoCommon facts worth checking before geometry code

The upstream notes below were verified against Rhino 8. On this project machine, the four listed members were also located in `C:\Program Files\Rhino 7\System\RhinoCommon.xml` (Rhino 7.0.20314.03001, checked 2026-09-27). Recheck the selected installation after an update.

- `Surface.IsoCurve(direction, constantParameter)`:
  - `direction = 0`: first parameter varies and second parameter stays constant
  - `direction = 1`: first parameter stays constant and second parameter varies
- `BrepFace.TrimAwareIsoCurve(direction, constantParameter)`:
  - pays attention to trims on faces
  - may return multiple curves
  - local XML states that `direction = 0` corresponds to an isocurve with constant `U`
- `Curve.DivideByCount(count, includeEnds)` returns curve parameters on success
- `BrepFace.OrientationIsReversed` tells you when face orientation is opposite the natural surface orientation
- `Surface.IsoCurve` and `BrepFace.TrimAwareIsoCurve` use direction descriptions that appear different in the Rhino 7 XML. Keep each API's own documented constant parameter convention; never reuse an integer direction across them without checking the intended U/V family.

## Original upstream author's machine snapshot

These are historical observations included by the upstream author. They do not describe the current Rhino 7 installation:

- `Rhino.exe` found at `C:\Program Files\Rhino 8\System\Rhino.exe`
- Rhino product version detected: `8.27.26019.16021`
- Grasshopper detected from `C:\Program Files\Rhino 8\Plug-ins\Grasshopper\Grasshopper.dll`
- Grasshopper file version detected: `8.27.26019.16021`
- Roslyn assemblies detected, including `Microsoft.CodeAnalysis.CSharp.dll`
- `McNeel.Python39.Runtime.dll` detected, which strongly indicates a Rhino 8 Python 3.9 runtime on this machine
- IronPython assemblies are also present, so legacy IronPython 2 support exists locally

## Current Rhino 7 installation checked for this port

- `Rhino.exe`: `C:\Program Files\Rhino 7\System\Rhino.exe`
- Rhino and Grasshopper file version: `7.0.20314.03001`
- RhinoCommon XML: `C:\Program Files\Rhino 7\System\RhinoCommon.xml`
- IronPython assembly: `C:\Program Files\Rhino 7\Plug-ins\IronPython\IronPython.dll`
- GhPython component: `C:\Program Files\Rhino 7\Plug-ins\Grasshopper\Components\GhPython.gha`
- Rhino 8 executable was not found during this check.

## High-risk geometry areas

Use extra care in these areas because they often produce valid-looking but semantically wrong code:

- trimmed face vs underlying surface
- U and V direction interpretation
- boundary sampling and seam or singularity handling
- methods that return arrays, parameters, or out values rather than the obvious geometry object
- face orientation and normal direction

## Community edge cases worth remembering

- `BrepFace.TrimAwareIsoCurve` can behave awkwardly near domain boundaries because the face domain can reflect the underlying surface while trims remove visible portions.
- Community discussions consistently show confusion around `Surface` vs `BrepFace`, especially when users refer to trimmed objects as "surfaces".

Reference:

- https://discourse.mcneel.com/t/rhinocommon-brepface-trimawareisocurve-does-not-work-on-domain-boundaries/45527

## Safe compatibility guidance

- For Rhino 7, default to legacy C# Script or IronPython 2.7 GhPython. Provide manual input/output setup alongside the script. Do not claim that Rhino 8 signature-driven port creation works in Rhino 7.
- For Rhino 7 ambiguous API lookup, pass `--rhino-major 7` or `--xml` pointing to its `RhinoCommon.xml`.

- For Rhino 8 C# node generation, prefer `C# 9.0 compatibility` as the safe baseline unless the user requests newer syntax and the local environment clearly supports it.
- For Rhino 8 Python node generation, prefer Python 3 unless Rhino 7 compatibility or IronPython 2 compatibility is explicitly requested.
- For Rhino 8 Python tasks that need component lifecycle hooks or explicit typed signatures, switch to SDK-Mode.

## Maintenance note

If Rhino is updated on the machine, rerun:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_python.ps1 .\scripts\detect_rhino_environment.py --rhino-major 7 --pretty
```

and refresh any version-specific notes if they change materially.

When a geometry API causes trouble, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_python.ps1 .\scripts\lookup_rhinocommon_docs.py --rhino-major 7 --member Surface.IsoCurve --member BrepFace.TrimAwareIsoCurve --pretty
```
