# Rhino 7 legacy C# Script: trimmed Brep isocurves as a tree

This is a copy-paste example for Rhino 7's **legacy C# Script** component. Its
exact body passed the detached Rhino 7 native probe with three output paths
and idle behavior; it was also compiled against installed Rhino 7 assemblies.
The visible Grasshopper canvas was not used for this check. Configure ports in the
component UI; pasting code does not create them.

| Direction | Name | Type hint | Access | Persistent default | Description |
| --- | --- | --- | --- | --- | --- |
| Input | `B` | Brep | Item | None | Brep whose selected trimmed face supplies the isocurves. |
| Input | `F` | Integer | Item | `0` | Zero-based face index. |
| Input | `N` | Integer | Item | `3` | Interior constant-U sample count, from 1 through 10000. |
| Output | `C` | — | — | — | `DataTree<Curve>`; path `{i}` contains all valid fragments from sample `i`, including an empty path when there are none. |
| Output | `out` | — | — | — | Keep the legacy diagnostic output while checking invalid inputs. |

Keep the editor-generated `RunScript(Brep B, int F, int N, ref object C)`
signature. Add these imports if the legacy editor has not already supplied them:

```csharp
using Rhino.Geometry;
using Grasshopper;
using Grasshopper.Kernel.Data;
```

Paste only this code inside the existing `RunScript` method:

```csharp
var tree = new DataTree<Curve>();
C = tree;

// A disconnected optional Brep is an idle state, not an error.
if (B == null) return;
if (!B.IsValid || F < 0 || F >= B.Faces.Count)
{
  Print("Select a valid Brep and face index.");
  return;
}
if (N < 1 || N > 10000)
{
  Print("N must be between 1 and 10000.");
  return;
}

BrepFace face = B.Faces[F];
Interval uDomain = face.Domain(0);
if (!uDomain.IsValid)
{
  Print("The selected face has no valid U domain.");
  return;
}

for (int i = 0; i < N; i++)
{
  GH_Path path = new GH_Path(i);
  tree.EnsurePath(path);
  double fraction = (i + 1.0) / (N + 1.0);
  double u = uDomain.T0 + fraction * (uDomain.T1 - uDomain.T0);
  Curve[] pieces = face.TrimAwareIsoCurve(0, u);
  if (pieces == null) continue;
  foreach (Curve piece in pieces)
    if (piece != null && piece.IsValid) tree.Add(piece, path);
}
```

The installed Rhino 7 `RhinoCommon.xml` says `direction = 0` means constant U,
and `TrimAwareIsoCurve` respects trims and may return multiple curves. It
returns `Curve[]` in the installed Rhino 7 API. The sample excludes U domain
endpoints so it does not intentionally sample a seam or boundary. It does not
merge coincident fragments. `OrientationIsReversed` concerns face orientation;
this UV sampling does not change direction from that flag. Check face normals
separately if later logic depends on them. Empty paths are created before the
API call, so missing fragments do not silently remove a requested sample.

Canvas acceptance requires a valid trimmed face, a face with a hole, an empty
sample location, disconnected `B`, invalid `F`, and invalid `N`. Record actual
paths, fragments, warnings, Rhino/Grasshopper versions, and document units.
