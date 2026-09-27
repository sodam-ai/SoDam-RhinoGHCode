---
name: sodam-rhinoghcode
description: Write Rhino 7 and Rhino 8 Grasshopper C# and Python script-node code matched to the installed runtime. Use for copy-paste GH node scripts, RhinoCommon lookup, version detection, idle-safe inputs, component IO setup, or persistent custom scripting rules.
---

# SoDam-RhinoGHCode

This skill generates scripts for actual Grasshopper components. For Rhino 7, the primary target is the installed, licensed Rhino 7 and its legacy C# Script or GhPython component. A small independent node evaluator is an optional development aid; it is not a substitute for native Grasshopper execution. This skill does not build compiled `.gha` plugins.

Use [references/parity-matrix.md](references/parity-matrix.md) to check which Rhino 7 claims have actual native evidence and which checks are auxiliary.

## Core workflow

1. Detect the local Rhino/Grasshopper scripting environment before writing code.
2. Use the version the user names. Otherwise use the detected installed version; if both 7 and 8 are installed, ask which version the script must run in. Never silently switch a Rhino 7 request to Rhino 8.
3. Read [references/default-rules.md](references/default-rules.md) every time.
4. Read [references/custom-rules.md](references/custom-rules.md) every time and treat it as higher priority than defaults.
5. Read [references/common-failure-modes.md](references/common-failure-modes.md) every time.
6. When geometry APIs are involved, read [references/rhinocommon-gotchas.json](references/rhinocommon-gotchas.json).
7. For version-sensitive behaviour and local API semantics, read [references/official-rhino-notes.md](references/official-rhino-notes.md).
   For Rhino 7, also read [references/rhino7-component-guide.md](references/rhino7-component-guide.md).
8. If the task uses ambiguous RhinoCommon geometry APIs, run `scripts/lookup_rhinocommon_docs.py` against the locally installed `RhinoCommon.xml` before writing the final code.
9. Generate code that is directly copy-pasteable into the requested node type. For Rhino 7, include the exact component-side port setup. Validate each new node in native Rhino 7 Grasshopper when access is available; do not treat auxiliary checks as native proof.

For Rhino 7 requests matching the supported `divide_polyline` or `bounds_points` operation, first run `python -B scripts/offline_node.py emit --operation <name> --language <csharp|ironpython>` from this skill directory. Copy the returned `code` field exactly into the answer, and use its `ports` fields for every input/output name, access, default, and description. Do not rewrite, shorten, or independently regenerate this verified body. If `emit` fails, report the failure instead of substituting an unverified body. This rule applies separately to each requested language.

## Optional independent checks

- Code generation, version inspection, and documentation lookup do not launch Rhino. Actual Rhino 7 and Grasshopper execution uses the user's working Rhino installation and its normal licensing. If Rhino cannot start because of an intermittent licensing error, record that error and leave native execution unverified until Rhino starts normally; do not report an offline result as native success.
- Run `python -B scripts/verify_tooling.py --rhino-major 7` once after installation or a tooling change. Reuse a recorded passing result while the installed files are unchanged; do not rerun the whole suite for every node request. For a new node, check its own code, ports, inputs, and result. Report `tooling_status` separately from `native_grasshopper_execution`.
- On Windows with Rhino 7 installed, this command also compiles the two bundled C# examples against the actual Rhino 7 `RhinoCommon.dll`. State that this proves those API signatures compile, not that any Grasshopper node ran or that arbitrary generated C# was checked.
- It also runs the two bundled GhPython examples in the installed IronPython 2.7 engine with point stubs. This verifies Python 2.7 execution of those bodies, not actual RhinoCommon objects, Grasshopper port wiring, or arbitrary generated scripts.
- For the supported `divide_polyline` and `bounds_points` operations, run `python -B scripts/offline_node.py run` with the respective `offline-polyline-sample.json` or `offline-bounds-sample.json` to calculate real output without Rhino. Use `emit --operation <name> --language csharp` or `--language ironpython` for Rhino 7 code and the matching port setup.
- Read [references/offline-compatibility.md](references/offline-compatibility.md) before claiming independent execution of any other operation. Reject unsupported operations explicitly; never silently pretend that a `rhino3dm` or static check ran a Grasshopper component.
- An installed Rhino 7 can be the target for generated code, but Rhino/Grasshopper execution is not a dependency of the independent evaluator. Do not attempt license bypass or call Rhino merely to satisfy an offline acceptance check.

## Detect environment first

Run for this Rhino 7 project:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_python.ps1 .\scripts\detect_rhino_environment.py --rhino-major 7 --pretty
```

If the script finds Rhino, use its results to drive the answer:

- Use detected Rhino and Grasshopper versions in the response.
- Use detected Python runtime information for Python nodes.
- Use detected compiler/runtime information as evidence of installed files, not proof that a component executed.
- For Rhino 7, use the legacy C# Script component or GhPython/IronPython 2.7 component. Do not emit Python 3 syntax, SDK-Mode, Rhino 8 unified Script component features, or C# 9 syntax for a Rhino 7 target.
- For Rhino 7 C#, provide code for the existing editor's `RunScript` body plus a precise parameter setup table. Keep helper methods in the editor's custom-code region. The component UI controls input/output names, type hints, access, defaults, and tooltips; editing a Rhino 8-style signature must not be presented as an automatic Rhino 7 IO setup method. The output parameter is `ref object`: initialize it with an empty typed list, build nonempty results in a typed local variable, and assign that list back to the output. Never call `.Add` or another collection method on the `object` output.
- For every newly generated Rhino 7 C# body, use `scripts/verify_rhino7_csharp_api.py --body-file` with the exact port-derived `--signature`, every stated `--using`, and `--helpers-file` when needed. Compile against the installed Rhino 7 assemblies before calling it paste-ready. If the compiler or Rhino 7 assemblies are unavailable, label compilation unverified. A successful compile does not prove the manual port setup or native Grasshopper result; check those separately when a running Rhino 7 session is available.
- For Rhino 7 GhPython, provide a script body and the same parameter setup instructions. Use Python 2.7/IronPython-compatible syntax and Rhino 7 RhinoCommon APIs.
- For Rhino 8, treat `C# 9.0 compatibility` as the safe default unless the user explicitly wants newer syntax and the detected environment supports it.

If detection fails or the requested version is absent:

- Report that the local version/runtime is unverified. Ask for the Rhino major version only if the user did not provide one. Never claim local compilation or execution from a fallback assumption.

## Mandatory semantic preflight for geometry tasks

Before generating code for geometry-heavy tasks, explicitly reason through these checks:

1. What is the true runtime geometry type?
   - `Surface`
   - `BrepFace`
   - `Brep`
   - `Curve`
   - `Mesh`
   - `SubD`
2. Does the task depend on trims, seams, singularities, face orientation, or periodic domains?
3. Are the API's direction flags or parameter meanings potentially ambiguous?
4. Does the API return a single object, an array, curve parameters, or a tree-shaped result?
5. Should boundaries be included or excluded?
6. Does `Single Item` access imply repeated per-item execution, or should the input be `List` or `Tree`?

When any answer is ambiguous, consult:

- `references/rhinocommon-gotchas.json`
- `references/official-rhino-notes.md`
- `scripts/lookup_rhinocommon_docs.py`

## Output policy

- Default to code-first answers.
- Return only the code when the user asks for code-only output.
- Keep the code inside one script component unless the user explicitly asks for a plugin or external assembly.
- Match the requested node family exactly and state the paste location:
  - Rhino 7 C# Script: `RunScript` body and separately labelled custom helper code; list the component-side IO setup.
  - Rhino 7 GhPython: IronPython 2.7 script body; list the component-side IO setup.
  - Rhino 8 C# Script component: `GH_ScriptInstance` structure
  - Rhino 8 Python 3 Script in simple cases: Script-Mode is acceptable
  - Rhino 8 Python 3 Script with component-like lifecycle or previews: use SDK-Mode
  - IronPython 2: avoid Python 3-only syntax and packages

## Grasshopper-specific defaults

- Missing or disconnected inputs are a normal idle state, not an error, unless the user explicitly wants required inputs.
- Initialize outputs early with safe empty defaults.
- Avoid orange/red states caused only by empty optional inputs.
- Remove default `out`/debug outputs unless the user asked for diagnostics.
- Name inputs and outputs deliberately. On Rhino 7, tell the user how to set them on the component before pasting the script; on Rhino 8, signature edits may create them.
- Prefer parameterized thresholds over hardcoded magic numbers. A request to divide a curve "into 5 segments" means an Integer Item `N` input with persistent default 5; the code must call `DivideByCount(N, true)`. Hardcode 5 only when the user explicitly requests a fixed, non-adjustable count.
- Choose `Item`, `List`, or `Tree` access deliberately when access shape affects behaviour.
- Prefer stable geometry representations over convenient ones:
  - `BrepFace` over `Surface` when trims matter
  - `Brep` plus `FaceIndex` when a multi-face object is likely
  - grouped output when one logical item can split into multiple geometry fragments
- For Rhino 7 C# grouped `DataTree<T>` output, list `using Grasshopper;` and `using Grasshopper.Kernel.Data;` in the imports section. Build the tree in a typed local variable and assign it to the `ref object` output. If every sampled location needs a branch even without valid fragments, call `tree.EnsurePath(path)` before the null/empty-fragment check; `Add` alone does not create an empty branch.
- For a Rhino 7 C# `DataTree<T>` input, iterate with `tree.BranchCount`, `tree.Path(i)`, and `tree.Branch(i)` (or `tree.Branch(path)`). `PathCount` belongs to `GH_Structure<T>`, not `DataTree<T>`; never mix these two tree APIs. Check preserved paths and item behavior in addition to compilation.
- When promising to preserve an input tree's paths, create every output path from that input before returning for a missing auxiliary input or invalid setting. A missing secondary tree may leave those branches empty, but must not erase them. Check this control-flow case separately from compilation.
- For a Rhino 7 trimmed Brep face with grouped isocurve fragments, read [references/rhino7-brep-tree-example.md](references/rhino7-brep-tree-example.md) for a complete port contract and a compiled legacy C# body. This exact body passed the detached Rhino 7 native probe; newly generated variants still require their own native checks.
- For new nodes, prefill safe practical defaults for optional numeric and boolean inputs so the node shows a useful result as soon as geometry is connected.
- Prefer non-zero sample values when they make the first test result visible immediately.
- Do not fabricate geometry, placeholder points, or demo curves; only seed parameter defaults.
- If the response recommends example values, supply the same defaults in the Rhino 7 component setup instructions or Rhino 8 generated script, as appropriate.
- Add clear descriptions for the node, inputs, and outputs. On Rhino 7, supply these as UI setup instructions rather than implying code alone installs them.
- Prefer practical natural-language descriptions that state the effect of a parameter, not just its type or short name.
- For counts, toggles, tolerances, and modes, describe what the user will get, for example: `N points will be created on the input curve.`

## C# rules

- For Rhino 8, generate `GH_ScriptInstance` code with `#region Usings`, `public class Script_Instance : GH_ScriptInstance`, and `private void RunScript(...)`.
- For Rhino 7, preserve its generated class and `RunScript` signature. Supply the method body and any helper code for the appropriate editor region. Do not paste a second `Script_Instance` class into the legacy editor.
- Keep code self-contained in one node.
- Use RhinoCommon carefully and verify ambiguous return types against [references/official-rhino-notes.md](references/official-rhino-notes.md).
- Prefer compatibility over novelty. For Rhino 8, write code that stays safe under a `C# 9.0` baseline unless the user asks otherwise.
- In geometry code, prefer small helper methods whose names restate semantics, for example `ParameterAtInteriorIndex` or `TryGetFace`.

## Python rules

- For Rhino 8, prefer Python 3 unless the user specifically asks for IronPython 2 or a Rhino 7-compatible legacy flow.
- For Rhino 7, use IronPython 2.7. Avoid f-strings, type annotations, Python 3-only packages, and Rhino 8 package directives.
- On Rhino 8, use SDK-Mode only when the task needs component-style hooks, typed `RunScript`, preview overrides, or stable IO generation from the signature.
- In Script-Mode, handle `None` and empty inputs explicitly to avoid runtime errors.

## Ambiguous RhinoCommon APIs

Treat these as high-risk and verify them against local docs or the gotcha registry before finalizing code:

- `Surface.IsoCurve`
- `BrepFace.TrimAwareIsoCurve`
- `Curve.DivideByCount`
- `Surface.FrameAt`, `NormalAt`, `ClosestPoint`
- `BrepFace.OrientationIsReversed`
- `UnderlyingSurface`
- `DuplicateFace`
- intersection and projection APIs that depend on tolerance or return arrays

Do not trust memory alone for these APIs when the user-facing result depends on exact semantics.

## Persisting user rules

If the user says any of the following, treat it as a persistent rule candidate:

- "this is a rule"
- "remember this"
- "always do it this way"
- "this is mandatory for me"
- "add this to the skill"
- Any equivalent Russian phrasing with the same intent

Then update `references/custom-rules.md` with a dated rule entry by running:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_python.ps1 .\scripts\update_custom_rules.py --rule "<rule text>" --source "user conversation"
```

When the rule affects generation strategy, also update this `SKILL.md` or [references/default-rules.md](references/default-rules.md) if the rule has become a stable global default rather than a user-specific preference.

## Clarification policy

Ask only when the choice changes the generated code materially and cannot be inferred:

- C# vs Python
- Python 3 vs IronPython 2
- Rhino 7 vs Rhino 8 when compatibility matters
- Script-Mode vs SDK-Mode for Python when lifecycle hooks matter

Otherwise make the safest assumption, state it briefly, and produce the working code.

## Recommended lookup commands

Use these when the task touches ambiguous APIs or geometry semantics:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_python.ps1 .\scripts\lookup_rhinocommon_docs.py --rhino-major 7 --member Surface.IsoCurve --member BrepFace.TrimAwareIsoCurve --pretty
```

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_python.ps1 .\scripts\lookup_rhinocommon_docs.py --rhino-major 7 --contains IsoCurve --contains OrientationIsReversed --pretty
```
