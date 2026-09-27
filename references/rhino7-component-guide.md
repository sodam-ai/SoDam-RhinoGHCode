# Rhino 7 Grasshopper component output guide

This guide applies only to the legacy C# Script and GhPython components in Rhino 7. Use `scripts/detect_rhino_environment.py --rhino-major 7` and `scripts/lookup_rhinocommon_docs.py --rhino-major 7` before version-sensitive geometry code.

## Required response for every new Rhino 7 node

1. Name the component (`C# Script` or `GhPython`) and the exact paste location.
2. Give a table for **each** input: name, type hint, Item/List/Tree access, optional or persistent default value, and tooltip.
3. Give a table for **each** output: name and tooltip. Say whether the default `out` is retained for diagnostics or removed.
4. Give the code for the existing editor: C# `RunScript` **body** with optional separately marked helper methods, or a GhPython **script body**. Do not paste Rhino 8's full `GH_ScriptInstance` class or Python SDK-Mode into Rhino 7.
5. Initialize outputs before checking optional inputs. An empty optional input should produce an empty result without a warning.
6. List a small Grasshopper canvas check with connected, disconnected, invalid, and multiple-item data. Report live execution only if actually observed.

In the Rhino 7 component, add and rename ports by zooming in on the component or using its parameter menu. Set the input's type hint, access and persistent data through that menu. Set the component and parameter descriptions in the UI. Code alone does not install these UI settings.

## Example: divide a curve into points

This example illustrates the output format. It is **not** evidence that a Rhino 7 canvas has run it.

| Input | Type hint | Access | Default | Tooltip |
| --- | --- | --- | --- | --- |
| `C` | Curve | Item | None | Curve to divide into equal-length segments. |
| `N` | Integer | Item | Persistent value `10` | Number of equal-length segments; output may contain `N + 1` points. |

| Output | Tooltip |
| --- | --- |
| `Pts` (C#) / `a` (GhPython; rename to `Pts` if desired) | Division points on the curve. |

Remove the default `out` output if console diagnostics are unnecessary. Set a component description such as `Divide a curve into equal-length segments and return the division points.`

### Legacy C# Script

Keep the editor-generated `RunScript` signature. Configure the ports so its signature contains `Curve C`, `int N`, and `ref object Pts`. Paste **only this body inside that method**:

Even if a request says "divide into 5 segments", set a persistent default of
5 on input `N` and use `N` in the method. The generated output `Pts` has type
`ref object`; adding directly to `Pts` will not compile. Build a local
`List<Point3d>` and assign it to `Pts` when complete.

```csharp
Pts = new List<Point3d>();
if (C == null || N < 1) return;
double[] parameters = C.DivideByCount(N, true);
if (parameters == null) return;
List<Point3d> points = new List<Point3d>();
foreach (double t in parameters) points.Add(C.PointAt(t));
Pts = points;
```

The usual legacy editor imports `System.Collections.Generic` and `Rhino.Geometry`. If those imports are absent, add them in its imports section. `Curve.DivideByCount` returns **parameters**, which are converted to points using `PointAt`.

For grouped C# results, `DataTree<T>` needs `using Grasshopper;` and `GH_Path` needs `using Grasshopper.Kernel.Data;`. Build the `DataTree<T>` locally and assign it to the `ref object` output. If the requested output contract includes a branch for a sample with no fragments, create its path with `tree.EnsurePath(path)` before checking whether the API returned any fragments. A loop that only calls `tree.Add(item, path)` loses empty branches.

For a `DataTree<T>` input, use `tree.BranchCount`, `tree.Path(i)`, and `tree.Branch(i)` to preserve each branch. `PathCount` is a `GH_Structure<T>` member and does not compile on `DataTree<T>` in the installed Rhino 7 Grasshopper assembly.

Before calling **any new C# node** paste-ready, save exactly the proposed `RunScript` body to a temporary UTF-8 file and compile it with the port-derived signature and the imports stated in the response. Include `--helpers-file` when the response has custom-code helpers:

```powershell
python -B scripts/verify_rhino7_csharp_api.py --body-file body.cs --signature 'Curve C, int N, ref object Pts' --using System.Collections.Generic --using Rhino.Geometry
```

The checker creates a temporary C# class and compiles against the installed Rhino 7 `RhinoCommon.dll`, `Grasshopper.dll`, and `GH_IO.dll`. It catches missing imports, invalid parameter types and C# syntax. It cannot verify the UI port settings, Tree path behavior, geometry output, or native component execution. For a complete C# source file, use `--source-file` instead of `--body-file`.

If the output contract promises all input paths, initialize the output tree and call `EnsurePath` for each path before any early return caused by a missing second input, invalid count, or absent matching branch. Compilation alone cannot establish this path-preservation behavior.

For a trimmed Brep face, use the complete [constant-U tree example](rhino7-brep-tree-example.md) as a Rhino 7 starting point. Its shown imports and body are compiled against installed Rhino 7 assemblies, while its port behavior still needs a canvas check.

### GhPython / IronPython 2.7

Set `C` to a Curve type hint, `N` to Integer, both with Item access. Rename the output to `Pts`, then paste this **whole script body**:

```python
Pts = []
if C is not None and N is not None and N > 0:
    parameters = C.DivideByCount(N, True)
    if parameters is not None:
        Pts = [C.PointAt(t) for t in parameters]
```

## Rhino 7 compatibility boundaries

- Python 3 and Python SDK-Mode belong to Rhino 8. Rework logic for IronPython 2.7 or choose the Rhino 7 C# component.
- The Rhino 8 unified Script editor's signature-driven port creation is not available in the legacy Rhino 7 component. Supply UI settings explicitly.
- Verify ambiguous geometry calls in Rhino 7's own `RhinoCommon.xml`; a Rhino 8 API note is not proof of Rhino 7 availability.
- This repo generates scripts and instructions. It does not install or run a Grasshopper component automatically.

Sources: [McNeel Rhino.Python versions](https://developer.rhino3d.com/guides/rhinopython/what-is-rhinopython/), [legacy GhPython input setup](https://developer.rhino3d.com/guides/rhinopython/ghpython-call-components/), [C# component parameter access](https://developer.rhino3d.com/guides/grasshopper/csharp-essentials/1-grasshopper-csharp-component/).
