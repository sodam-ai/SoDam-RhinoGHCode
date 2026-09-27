# Sample Environment Report

This is a sample of the environment information the helper scripts can derive before Codex writes a Grasshopper node script.

## Detected environment

- Rhino major version: `8`
- Rhino version: `8.27.26019.16021`
- Grasshopper version: `8.27.26019.16021`
- Preferred Python runtime: `Python 3.9`
- IronPython detected: `true`
- Roslyn bridge detected: `true`
- C# compatibility recommendation: `C# 9.0`

## What Codex should infer

- default Rhino target should be Rhino 8
- default Python target should be Python 3
- default C# target should stay within a C# 9.0-compatible subset
- if the user asks for old compatibility, IronPython 2 remains available as an explicit fallback
- if the user says a behavior is a lasting rule, it should be appended to `references/custom-rules.md`

## Example generation consequence

If the user asks:

`Write a Grasshopper C# script that divides curves into points and stays neutral when no curves are connected`

Codex should:

- detect Rhino 8
- use the Grasshopper C# script shape based on `GH_ScriptInstance`
- initialize outputs before validation
- early-return on empty optional inputs without warnings
- treat `Curve.DivideByCount(...)` carefully and convert parameters to points explicitly
