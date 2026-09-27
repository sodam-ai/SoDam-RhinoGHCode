# One-pass Rhino 7 native acceptance

This records the **native component** check. It does not replace the
already passing installer, independent calculation, Rhino 7 API compile, or
IronPython stub checks. Do not open or bake into the existing Rhino model, or
change Rhino licensing, global settings, or other Grasshopper definitions.
No separate project folder is needed.

## Recommended one-command native check

With Rhino 7 and Grasshopper already open, enter this in the **Rhino command
line** once:

```text
_-RunPythonScript "D:\AI_Dev_Work\2026y\26y_09m_30d_SoDam-RhinoGHCode\references\rhino7-native-probe.py"
```

The script creates a detached, unsaved `GH_Document`, runs the four emitted
C#/GhPython point nodes and the C# trimmed Brep Tree example, and writes
`D:\AI_Dev_Work\2026y\26y_09m_30d_SoDam-RhinoGHCode\rhino7-native-probe-result.json`.
It does not add geometry to the Rhino document or visible Grasshopper canvas.
The corrected probe passed on Rhino `7.0.20314.3001`: all four point nodes
returned their expected values, and the C# trimmed Brep tree had paths
`{0}`, `{1}`, `{2}` with branch counts `1`, `2`, `1`. All five idle checks
passed without warnings or errors. The result is recorded in
`rhino7-native-probe-result.json` and preserved in
`references/rhino7-native-probe-result-2026-09-27.json`. This proves these five cases and their idle
behavior in Rhino 7; it does not establish arbitrary RhinoCommon parity. If a
future run fails before it writes a report, use the Rhino command-line error
text. The manual canvas route below remains available for visual inspection.

## Prepare one isolated canvas

1. Close the Grasshopper tutorial dialog and select **File > New** in
   Grasshopper. Keep the user's current Rhino document open and untouched.
2. Add one Rhino 7 **legacy C# Script** component as a test fixture. Give it
   four outputs named `PolyPts`, `BoundsPts`, `B`, and `Status`. Its default
   inputs can remain disconnected; the fixture body does not use them.
   Open `rhino7-native-fixture.cs`, add its listed imports if absent, and paste
   only the statements inside its `RunScript` method into the editor-generated
   method. Connect a Panel to `Status`. Continue only if the panel says
   `PASS: planar face with an inner trim`.
3. Use `python -B scripts/offline_node.py emit --operation divide_polyline
   --language csharp` and the same command with `ironpython`; repeat for
   `--operation bounds_points`. Each command prints the **exact** port names,
   type hints, access, descriptions, paste location, and body. Configure four
   separate legacy components accordingly. Connect `PolyPts` to each division
   node's `P` and `BoundsPts` to each bounds node's `P`. Set both division `N`
   inputs to persistent integer `3` (the emitted default is `10`). Remove
   unused default diagnostic outputs only after recording any errors.

   The `emit` command prints JSON, so its escaped `code` string is **not**
   directly pasteable. In PowerShell, copy the decoded body for one node with:

   ```powershell
   python -B scripts/offline_node.py emit --operation divide_polyline --language csharp | ConvertFrom-Json | Select-Object -ExpandProperty code | Set-Clipboard
   ```

   Change `--operation` and `--language` for the other three nodes. Read the
   matching JSON once for the port settings; then paste the decoded clipboard
   content into the editor location named by `paste_location`.
4. Add one more legacy C# Script component using
   `rhino7-brep-tree-example.md`. Connect the fixture `B` to its `B`; set
   persistent `F=0` and `N=3`. Keep its `out` diagnostic output during this
   test. No input references the existing Rhino model.

For the installed Codex plugin's use check, make one request per language using
`Use $sodam-rhinoghcode` and explicitly ask for the Rhino 7
`divide_polyline` sample above, a full port table including descriptions, and
an idle-safe script body. Compare each response against the emitter's exact
port contract and expected points. A response that omits a port description,
uses Rhino 8-only syntax, or gives incorrect results is a failed use check;
do not silently repair that response before recording the failure. The
emitted-code canvas checks remain separate from this model-response check.

## Fixed observations and pass conditions

| Component | Connected input | Required native output |
| --- | --- | --- |
| C# polyline division | `[(0,0,0),(2,0,0),(2,4,0)]`, `N=3` | Four ordered points: `(0,0,0)`, `(2,0,0)`, `(2,2,0)`, `(2,4,0)` |
| GhPython polyline division | Same | Same four ordered points |
| C# point bounds | `[(4,-2,6),(-1,8,3),(2,0,-5)]` | `Min=(-1,-2,-5)`, `Max=(4,8,6)` |
| GhPython point bounds | Same | Same `Min` and `Max` |
| C# trimmed Brep tree | Fixture's `B`, `F=0`, `N=3` | Paths `{0}`, `{1}`, `{2}` exist, even if a path contains no curves; at least one sample through the circular inner trim returns split fragments. Record every branch's count rather than assuming an exact split count. |

Compare point coordinates within `1e-6` document units. If the fixture reports
`FAIL`, stop and record that failure; do not substitute an untrimmed Brep.
For each of the four point nodes, disconnect only `P`: its outputs should be
empty/null and the component should not be orange or red merely for that idle
input. Reconnect `P`. Set division `N=0`: output should be empty, without a
runtime exception. For the tree node, disconnect `B` and check an empty tree
without a runtime warning; reconnect it, then test invalid `F` and `N` and
record the diagnostic output. Restore `F=0`, `N=3` after observing it.

Capture one screenshot of the whole canvas with output Panels, plus a close-up
of any failing component and its error text. Record Rhino and Grasshopper
versions and document units. A screenshot of the editor alone is not output
evidence. Save a copy of the test definition in this existing project only if
the user wants to keep it; the disposable canvas need not be saved.

## Stop rule

Mark only the observed cases as `pass`. If one case fails, fix that concrete
case and retest it once; leave unrelated passing cases alone. Do not repeat the
full offline/compile suite or claim arbitrary RhinoCommon/Grasshopper methods
work because these examples pass. An arbitrary new operation still needs its
own exact API and behavior check. The independent evaluator is only an
optional aid; it does not replace native Rhino 7 Grasshopper execution.
