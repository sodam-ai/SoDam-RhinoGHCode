# Rhino 7 acceptance gates

Use the upstream skill behavior as the baseline and actual Rhino 7 Grasshopper
components as the final execution target. Record each gate separately; a pass
at one level does not imply a pass at the next level. The auxiliary commands
below do not start Rhino. Native checks use the user's normally licensed Rhino.

| Gate | How to check | Pass condition | Current status |
| --- | --- | --- | --- |
| Skill structure and version routing | `python -B scripts/verify_tooling.py` | Structure, rules, installer safety, version tests, and both offline samples pass on Windows and Linux | Local portable check passed; hosted CI result not observed |
| Existing skill installation | `python -B scripts/install_skill.py --source . --target "$env:USERPROFILE\.codex\skills" --plan`; after specific approval, `--sync-existing --backup-file <new-backup.zip>` | Canonical skill name resolves to the intended directory; backup is verified before updates; existing user rules and installed-only files are preserved | Passed on 2026-09-27: the user-approved sync updated 32 files, then one detector file after a compatibility fix. Each synchronization created and verified a ZIP backup. A later source update needs a fresh plan/sync. The active skill catalog lists `grasshopper-script-nodes` as global. |
| Live Codex skill generation | Invoke the skill with the prompts below in an isolated Codex task | Both Rhino 7 languages return copy-paste bodies plus complete port setup, idle handling, exact API evidence and no Rhino 8 syntax | The latest explicit installed-skill response for `divide_polyline` returned both C# and IronPython bodies exactly matching `offline_node.py emit`, including all port descriptions. A fresh generic CLI request on 2026-09-27 did not select the skill: the CLI reported that its skills context budget was exceeded and omitted 1,061 skills. Its generated C# answer was not native-tested. Name `$grasshopper-script-nodes` explicitly for reliable use. |
| Installed Rhino 7 metadata | `python -B scripts/detect_rhino_environment.py --rhino-major 7` | Exact selected major is 7; Grasshopper, GhPython and IronPython files are present | Passed on this Windows installation; file presence only |
| Rhino 7 API documentation | `python -B scripts/lookup_rhinocommon_docs.py --rhino-major 7 --member Curve.DivideByCount` | Exact requested member found in Rhino 7 XML, without fallback to Rhino 8 | Passed for the bundled lookup set; API behavior not executed |
| Independent point results | `python -B scripts/offline_node.py run offline-polyline-sample.json` and `python -B scripts/offline_node.py run offline-bounds-sample.json` | Expected ordered points and XYZ bounds returned; invalid specs fail | Passed for both supported operations |
| Emitted code and port identity | `python -B -m unittest discover -s scripts -p test_*.py` | CLI outputs exactly the same four C#/IronPython bodies and port contracts used by tests | Passed in the installed skill on 2026-09-27: 35 script tests with one platform skip, plus all six preserved installed-only tests. Three preserved tests initially failed because the detector had dropped old API names; compatibility functions were restored before the final pass. |
| Rhino 7 C# compatibility | `python -B scripts/verify_rhino7_csharp_api.py` | Both emitted bodies and the trimmed Brep/Tree patterns compile against installed Rhino 7 `RhinoCommon.dll`, `Grasshopper.dll`, and `GH_IO.dll` | Passed locally; four built-in compile cases plus the documented Brep Tree example, no component execution |
| Specific generated C# response | Put the response's imports, editor method signature, body and helpers in one `.cs` wrapper, then run `python -B scripts/verify_rhino7_csharp_api.py --source-file <wrapper.cs>` | The complete supplied source compiles against installed Rhino 7 DLLs; report names `provided_source` | The recorded Case 6 answer failed with CS0246; adding only `using Grasshopper;` passed. The fresh first installed-skill answer failed with CS1061 (`DataTree<T>.PathCount`). The second and third installed-skill answers passed compilation with `provided_source`. The second failed the missing-`F` path-preservation contract on code inspection; the third corrected that order. No canvas run was performed. |
| Rhino 7 IronPython compatibility | `python -B scripts/verify_rhino7_ironpython.py` | Actual installed interpreter is Python 2.7; both bodies handle normal, empty, degenerate and invalid test inputs | Passed with point stubs; no RhinoCommon objects |
| Native Grasshopper result | Run the one-command detached-document probe in `rhino7-native-acceptance.md`; inspect its JSON and use the manual canvas route only if needed | Correct type hints, Item/List/Tree access, disconnected behavior, output and component status | Directly rerun through the existing Rhino 7 COM interface on 2026-09-27. Rhino `7.0.20314.3001`: all four emitted C#/GhPython point nodes and the C# Brep Tree passed connected and idle cases with no errors. The Tree returned paths `{0}`, `{1}`, `{2}` with counts `1`, `2`, `1`. The Rhino process count remained one. A separate visible test definition then displayed and solved all five nodes; `rhino7-visible-check-result.json` records 5/5 expected outputs, no warnings or errors, and Rhino object count 67 before and after. The test definition was closed without saving; `rhino7-visible-cleanup-result.json` records zero remaining GH documents and the same 67 Rhino objects. This verifies these fixed examples, not arbitrary future nodes. |
| Optional independent evaluator beyond two operations | Per-operation independent implementation and conformance fixtures | Explicitly named operation, real independent result, tolerances, failures and representative geometry compared | Not implemented; not a completion gate for the native Rhino 7 skill |

## Live skill response cases

For a local response smoke test, explicitly tell an ephemeral Codex session to
read this project's `SKILL.md`; this tests instruction-following, not automatic
skill discovery. Run the full installed-skill tests only after installation at
the intended destination, while preserving existing custom rules. Record each
prompt, full answer and selected Rhino version. Check code and ports separately.

Local smoke test on 2026-09-27: six explicit, ephemeral, read-only Codex
responses are recorded with their prompts in
[codex-response-smoke-test.md](codex-response-smoke-test.md). The first C#
answer hardcoded 5 and omitted `N`; after an explicit rule was added to
`SKILL.md`, a fresh answer with an additional prompt clarification exposed `N`.
The identical original prompt still hardcoded 5 and also called `.Add` on an
`object` output. After strengthening the C# rule, another run of that same
prompt exposed `N`, built a typed local list, and compiled against the local
Rhino 7 RhinoCommon.dll. The GhPython answer used Python 2.7-compatible syntax
and an empty idle result. The sixth Brep response correctly identified
`TrimAwareIsoCurve(0, u)` and `Curve[]`, but failed a Rhino 7 compile because
its import list omitted `using Grasshopper;`. Its claimed empty sample paths
were also absent from the code. A corrected `DataTree<Curve>` pattern using
`EnsurePath` compiled against installed Rhino 7 and Grasshopper DLLs. A
subsequent Tree response request was rejected by automatic approval review
because the request could transmit local skill files to an external model;
no alternate route was used. These are response and compilation checks, not
native Grasshopper runs. The CLI read-only
sandbox blocked temporary-file checks, while
`python -B scripts/verify_tooling.py --rhino-major 7` passed 27 local tests at that time; the current installed-skill run passes 35 script tests plus six preserved tests
outside that sandbox.

1. Request a Rhino 7 legacy C# Script node that divides an input Curve into
   points. Require a `RunScript` body, a complete port table, disconnected
   input behavior, and the Rhino 7 `Curve.DivideByCount` return type.
2. Request the same Rhino 7 node in GhPython. Require IronPython 2.7 syntax,
   a whole script body, the port table, and no Python 3 or SDK-Mode features.
3. Request a trimmed Brep face isocurve. Require the selected Rhino 7 XML
   member, the intended U/V family, array handling, trim and face orientation
   notes, and a concrete output shape. An ambiguous API must not be guessed.
4. Request a node with a Tree input and grouped outputs. Require branch path
   preservation and explicit Item/List/Tree settings; mark the result
   unverified until tested on a native canvas.
5. Add a custom rule in a disposable copy of the skill, reload it, and request
   another node. Verify the new rule is applied without changing the original
   rule file. Do not write a test rule into the user's real preference file.

For C# response cases, compile the **whole supplied answer** after placing its
listed imports, `RunScript` signature, body, and helpers in a plain class wrapper.
Use `--source-file` above. Do not add missing imports or fix body code before the
first compile; record that failure, then check any correction separately. A
passing wrapper compile verifies syntax and referenced API signatures only.

## Native component test procedure when Rhino 7 is normally usable

The recommended one-command probe, manual canvas fallback, fixed inputs,
expected outputs, and a project-local trimmed-Brep fixture are in
[rhino7-native-acceptance.md](rhino7-native-acceptance.md)
and [rhino7-native-fixture.cs](rhino7-native-fixture.cs). The fixture compiled
against the installed Rhino 7 assemblies on 2026-09-27. The separate detached
native probe passed five fixed cases, recorded in
`rhino7-native-probe-result-2026-09-27.json`.

1. Work in a copy of a Grasshopper document. Use the port contract from
   `offline_node.py emit` to configure the legacy C# Script and GhPython
   components. Record the Rhino and Grasshopper version and document units.
2. For each of the four generated bodies, compare connected sample output with
   the independent sample, then disconnect `P`, supply degenerate points, and
   supply invalid data. Record output values and warning/error state, not just
   a screenshot of code in an editor.
3. Test `Item`, `List`, and `Tree` behavior with separate sample data where a
   request uses those access modes. Preserve branch paths and item order in the
   expected result. A List test cannot establish Tree behavior.
4. For new Curve, Surface, Brep, Mesh or SubD operations, verify the exact Rhino
   7 XML signature, coordinate system, document units and tolerance, then use
   representative boundaries, seams, trims and orientation cases as applicable.
5. Attach the observed input, expected output, actual output, component state,
   and Rhino/Grasshopper versions to the corresponding matrix row. Change its
   status to verified only for the cases actually observed.

Native checks must use Rhino through its normal operation. This project does
not bypass activation or treat standalone IronPython, XML lookup, compilation,
or third-party geometry results as a Grasshopper canvas run.
