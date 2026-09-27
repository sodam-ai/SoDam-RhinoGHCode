# Common Grasshopper And RhinoCommon Failure Modes

This file summarizes the failure patterns that most often cause generated Grasshopper script code to be "almost right" but still fail in practice.

Use it as a defensive checklist, not as a complete RhinoCommon reference.

## 1. Geometry representation mismatch

The user asks about a geometric concept, but the code uses the wrong runtime representation.

Common examples:

- `Surface` used where trims matter and the task really needs `BrepFace`
- `UnderlyingSurface()` used even though the user cares about the visible trimmed face
- `Brep` used without choosing the correct face
- `Curve` code written for a polyline-only case

Typical symptoms:

- lines appear offset or extend beyond visible boundaries
- results are topologically correct in UV-space but visually wrong in model space
- type conversion errors such as `GH_Surface` to `BrepFace`

Prevention:

- identify the real runtime type first
- prefer `BrepFace` when trims matter
- prefer `Brep + FaceIndex` when multiple faces are plausible

## 2. Ambiguous API semantics

The method name looks obvious, but its flags or return values are easy to misread.

Common examples:

- `Surface.IsoCurve(direction, constantParameter)`
- `BrepFace.TrimAwareIsoCurve(direction, constantParameter)`
- `Curve.DivideByCount`
- face orientation APIs

Typical symptoms:

- code compiles but produces the wrong geometry family
- "U" and "V" labels are swapped
- code expects a single curve and receives an array
- points are expected but curve parameters are returned

Prevention:

- verify method semantics against local `RhinoCommon.xml`
- restate the meaning of each flag in plain language before coding
- prefer helper methods that encode intent

## 3. Boundary and domain mistakes

The algorithm samples valid parameter domains incorrectly.

Common examples:

- including domain boundaries when only interior samples are expected
- sampling seam or singularity parameters without handling them
- assuming the face domain equals the active trimmed area
- relying on exact domain endpoints for trim-aware queries

Typical symptoms:

- duplicated edge curves
- missing or null results at boundaries
- one family of curves appears to "slide" onto an edge

Prevention:

- decide explicitly whether boundaries are included
- use interior sampling when the user asks for internal grid lines
- treat seams, singularities, and domain boundaries as special cases

## 4. Grasshopper access-shape mistakes

The code is correct for one item shape but the component executes with another.

Common examples:

- `Single Item` access when the logic assumes a whole list
- list input but code expects one item
- flat list output where each logical input item can split into many parts

Typical symptoms:

- repeated execution surprises
- data conversion warnings
- loss of grouping information

Prevention:

- choose `Item`, `List`, or `Tree` deliberately
- use grouped output when one logical entity can produce multiple geometry fragments
- mention expected access shape in the answer when it matters

## 5. Optional input and idle-state mistakes

The script turns orange or red when the user simply has nothing connected yet.

Common examples:

- dereferencing null inputs
- treating disconnected optional inputs as an error
- failing to initialize outputs before validation

Typical symptoms:

- unpleasant idle states
- poor user experience
- hard-to-debug script output

Prevention:

- initialize outputs first
- return early with safe empty values
- only warn when data is present but invalid

## 6. Tolerance and proximity mistakes

Geometry code silently depends on tolerance but uses hardcoded or omitted values.

Common examples:

- curve or surface projection
- intersection routines
- equality checks on points, vectors, and parameters

Typical symptoms:

- results differ between files
- "works on my model" behaviour
- unexpected nulls or duplicate geometry

Prevention:

- expose tolerance as an input when it changes behavior materially
- use Rhino tolerances deliberately instead of magic constants

## 7. Orientation and frame mistakes

The geometry exists, but local orientation assumptions are wrong.

Common examples:

- ignoring `BrepFace.OrientationIsReversed`
- assuming normals always match face orientation
- building frames without checking surface orientation or seams

Typical symptoms:

- flipped normals
- mirrored offsets
- geometry appears correct but downstream operations break

Prevention:

- inspect orientation-related properties for face-based tasks
- document whether the code follows natural surface orientation or Brep face orientation

## 8. User-language to API-language translation mistakes

The user's words do not map 1:1 to RhinoCommon vocabulary.

Common examples:

- "generatrices" can mean isocurves, section lines, rulings, or contour-like divisions depending on context
- "surface" in user language may actually mean a trimmed face
- "points on curve" may mean equal chord points, equal arc-length points, or control points

Typical symptoms:

- code solves a nearby problem, not the real one
- output feels plausible but unhelpful

Prevention:

- translate the request into explicit geometric semantics before coding
- when terms are overloaded, choose the safest interpretation and state it briefly

## High-value default checks

Before finalizing a Grasshopper script, verify:

1. The runtime geometry type is correct.
2. Trims, seams, singularities, and orientation have been considered when relevant.
3. Ambiguous API members were checked against local docs or the gotcha registry.
4. Return types match reality: single item, array, parameters, points, or grouped trees.
5. Boundaries and tolerances were chosen deliberately.
6. The node remains neutral when optional inputs are empty.

## 9. Plane fitting return-type mismatch

`Plane.FitPlaneToPoints(...)` returns `PlaneFitResult`, not `bool`.

Typical symptom:

- `Operator '!' cannot be applied to operand of type 'PlaneFitResult'`

Prevention:

- compare the result to `PlaneFitResult.Success`
- for three known non-collinear triangle vertices, prefer `new Plane(A, B, C)` and check `plane.IsValid`
