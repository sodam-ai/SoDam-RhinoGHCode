# SoDam-RhinoGHCode

## English guide

### Contents

1. [Purpose](#en-1)
2. [Prerequisites and downloads](#en-2)
3. [Local marketplace installation](#en-3)
4. [Five-minute start](#en-4)
5. [Workflow and operation](#en-5)
6. [Commands](#en-6)
7. [Update summary](#en-7)
8. [Files and architecture](#en-8)
9. [Security and data flow](#en-9)
10. [Evidence and troubleshooting](#en-10)
11. [FAQ](#en-11)
12. [License, copyright, commercial use](#en-12)
13. [Sources](#en-13)

<a id="en-1"></a>
### 1. Purpose

Grasshopper is Rhino's visual node system. A script node is a box into which you paste code. This repository packages a **Codex skill as a local marketplace plugin** to produce version-specific Grasshopper node code and exact port setup instructions. It is **not** a compiled Rhino .gha plugin, Rhino UI automation, or a Rhino license bypass.

For Rhino 7 it produces legacy C# Script <code>RunScript</code> bodies or GhPython/IronPython 2.7 bodies, with input/output names, type hints, Item/List/Tree access, defaults, and descriptions. You set those ports in Rhino 7 manually. Rhino 8 C# <code>GH_ScriptInstance</code>, Python 3, and IronPython 2 guidance remains; native Rhino 8 execution has not been checked on this machine. Two optional standard-library point-list calculations, equal-length open-polyline division and 3D axis-aligned bounds, run without Rhino and do **not** prove Grasshopper execution.

This document reflects project files and local records checked on 2026-09-27. The public source is [sodam-ai/SoDam-RhinoGHCode](https://github.com/sodam-ai/SoDam-RhinoGHCode). Run the installation commands inside your downloaded project folder.

<a id="en-2"></a>
### 2. Prerequisites and downloads

| Purpose | Requirement | Where to get it |
| --- | --- | --- |
| Generate code in Codex | This project folder, a Codex desktop/CLI release with plugin commands, an account that can access Codex | Follow [official Codex guidance](https://developers.openai.com/codex/). Check <code>codex --version</code> and <code>codex plugin --help</code> in PowerShell. |
| Build the plugin and run optional calculations | Python 3.10 or newer; project verification used 3.12 | Download from [Python for Windows](https://www.python.org/downloads/windows/), then check <code>py -3.12 --version</code>. An existing 3.10+ <code>python</code> may be used after checking its version. |
| Execute nodes in Rhino 7 | A working Rhino 7 installation, an applicable valid license, and its Grasshopper | Use the [official McNeel downloads and archives](https://www.rhino3d.com/en/download/). No redownload is needed if already installed. |
| Read this guide | A Markdown viewer or web browser | Open <code>README.md</code> in an editor or <code>README.html</code> in a browser. The HTML body is readable offline. |

Get this project from its [GitHub page](https://github.com/sodam-ai/SoDam-RhinoGHCode) with **Code → Download ZIP**, then extract it. If Git is installed, use the `git clone` command below. The [DariyXYZ upstream repository](https://github.com/DariyXYZ/grasshopper-script-nodes) is the base project, **not** the download for this Rhino 7 adaptation. Open PowerShell from Windows Start and paste one command per line. Review the source before running scripts.

<a id="en-3"></a>
### 3. Local marketplace installation

On this PC, a check on 2026-09-27 showed <code>sodam-rhinoghcode@sodam-rhinoghcode</code> installed and enabled. First run <code>codex plugin list</code>; if it is still present, continue to section 4. For a first installation or refresh after source changes:

~~~powershell
git clone https://github.com/sodam-ai/SoDam-RhinoGHCode.git
Set-Location -LiteralPath '.\SoDam-RhinoGHCode'
py -3.12 -B scripts/build_plugin_bundle.py
py -3.12 -B scripts/build_plugin_bundle.py --check
codex plugin marketplace add .
codex plugin add sodam-rhinoghcode@sodam-rhinoghcode
codex plugin list
~~~

The first two lines download and enter the project. For a ZIP download, open PowerShell in the extracted folder and start with the third line. The build copies current skill sources into the plugin bundle; <code>--check</code> must pass. The dot registers the **current directory as a local marketplace**, not as a public listing. <code>plugin add</code> installs its plugin. Confirm the exact ID and enabled state in <code>plugin list</code>. Open a new Codex chat and explicitly start with <code>$sodam-rhinoghcode</code>; restart Codex if a newly installed skill is not visible in an existing session.

This plugin has no separate MCP server, plugin API key, or plugin-specific Rhino authentication. Running Rhino/Grasshopper natively still needs normal Rhino authorization. Codex account access is separate.

<a id="en-4"></a>
### 4. Five-minute start

1. In a new Codex chat, send: “<code>$sodam-rhinoghcode Write a Rhino 7 Grasshopper GhPython node for the bounds of a point list. Include exact input/output names, Point3d type hints, List/Item access, paste location, and empty-input behavior.</code>”
2. Confirm the answer targets **Rhino 7 / GhPython / IronPython 2.7**. Do not paste Rhino 8 Python 3/SDK code into a Rhino 7 node.
3. Launch Rhino 7 normally and type <code>_Grasshopper</code> in its command line. Place a **GhPython** component on a new Grasshopper canvas.
4. Set port names, type hints, and access in the component UI using the answer's table. Paste the code into the GhPython editor. Pasting code alone does not change Rhino 7 port settings.
5. Connect a small point list and inspect values and runtime messages. Disconnect it and check that the output clears. Save only to the Grasshopper file you intend. Use a copy before testing against an important Rhino model.

For C#, request <code>C# Script</code> instead and paste **only the returned RunScript body** inside the editor-generated method. An <code>emit</code> JSON <code>code</code> string must be decoded first with the command in section 6.

<a id="en-5"></a>
### 5. Workflow and operation

Request with target Rhino version and node language → Codex reads the installed skill, default and custom rules, and failure notes → if needed, it inspects local Rhino installation metadata and <code>RhinoCommon.xml</code> → it responds with version-appropriate code and a port table → you set ports, paste code, and run real inputs in Rhino 7.

Examples: “<code>$sodam-rhinoghcode Rhino 7 C# Script: output Brep face curves as a Tree; include B/F/N ports and idle behavior.</code>” Or: “<code>$sodam-rhinoghcode Rhino 7 GhPython: return an empty list when disconnected.</code>” A Rhino 8 Python 3 request is supported as guidance, but native Rhino 8 execution is unverified here. Name the skill explicitly: a generic “Grasshopper code” prompt might not select it. Every newly generated node requires its own live test. The five fixed passing examples do not prove arbitrary future code.

<a id="en-6"></a>
### 6. Commands

Run these in the project root in PowerShell. If <code>python</code> points to verified Python 3.10+, it can replace <code>py -3.12</code>.

| Task | Command |
| --- | --- |
| Show Codex plugin state | <code>codex plugin list</code> |
| Check source and plugin bundle | <code>py -3.12 -B scripts/build_plugin_bundle.py --check</code> |
| Detect Rhino 7 | <code>py -3.12 -B scripts/detect_rhino_environment.py --rhino-major 7 --pretty</code> |
| Look up a Rhino 7 API member | <code>py -3.12 -B scripts/lookup_rhinocommon_docs.py --rhino-major 7 --member Surface.IsoCurve --pretty</code> |
| Run sample polyline division | <code>py -3.12 -B scripts/offline_node.py run offline-polyline-sample.json</code> |
| Run sample 3D bounds | <code>py -3.12 -B scripts/offline_node.py run offline-bounds-sample.json</code> |
| Emit C# code and ports | <code>py -3.12 -B scripts/offline_node.py emit --operation bounds_points --language csharp</code> |
| Emit GhPython code and ports | <code>py -3.12 -B scripts/offline_node.py emit --operation bounds_points --language ironpython</code> |
| Run local tooling checks | <code>py -3.12 -B scripts/verify_tooling.py --rhino-major 7</code> |

Use <code>--operation divide_polyline</code> for division. The <code>emit</code> response is JSON. To copy its decoded <code>code</code> field:

~~~powershell
py -3.12 -B scripts/offline_node.py emit --operation bounds_points --language ironpython |
  ConvertFrom-Json | Select-Object -ExpandProperty code | Set-Clipboard
~~~

This **replaces the clipboard**; preserve anything important first. Unsupported operations/languages and invalid JSON fail with an error. The independent evaluator supports only the two documented point-list operations. See [its scope and limits](references/offline-compatibility.md).

<a id="en-7"></a>
### 7. Update summary

<details>
<summary>Expand: current implementation and changes</summary>
<p><strong>Rhino 7 adaptation:</strong> Added legacy C# Script and GhPython/IronPython 2.7 paste locations and manual port guidance to the upstream Rhino 8 emphasis. Rhino 8 guidance remains.</p>
<p><strong>Codex packaging:</strong> Added the local marketplace catalog, plugin manifest, and <code>sodam-rhinoghcode</code> skill bundle. The old standalone skill path remains an auxiliary route; this guide uses the marketplace route.</p>
<p><strong>Evidence:</strong> Two point operations, their four C#/GhPython nodes, and one C# Brep Tree node passed fixed live Rhino 7 tests, including idle input behavior. This does not establish Rhino 8 or arbitrary-node behavior.</p>
<p><strong>README:</strong> Added bilingual beginner instructions, local installation, data flow, rights boundaries, and a matching HTML rendering. This is a feature summary, not a complete dated Git history.</p>
</details>

After changing skill sources, run <code>build_plugin_bundle.py</code> and <code>--check</code>, reinstall with <code>codex plugin add sodam-rhinoghcode@sodam-rhinoghcode</code>, check <code>codex plugin list</code>, and start a new chat. Back up and review <code>references/custom-rules.md</code> before editing personal rules. The project source and installed plugin cache are separate copies.

<a id="en-8"></a>
### 8. Files and architecture

| Project-relative path | Purpose |
| --- | --- |
| <code>README.md</code> / <code>README.html</code> | Same guide in Markdown and browser-readable HTML |
| <code>.agents/plugins/marketplace.json</code> | Local marketplace catalog |
| <code>plugins/sodam-rhinoghcode/.codex-plugin/plugin.json</code> | Plugin name, version, skill path |
| <code>plugins/sodam-rhinoghcode/skills/sodam-rhinoghcode/</code> | Bundled skill installed by Codex |
| <code>SKILL.md</code> | Main skill instructions |
| <code>references/rhino7-component-guide.md</code> | Rhino 7 ports and paste locations |
| <code>references/parity-matrix.md</code> | Upstream comparison and evidence boundary |
| <code>references/custom-rules.md</code> | User-added generation preferences |
| <code>scripts/offline_node.py</code> | Two point-list operations and Rhino 7 code emission |
| <code>scripts/build_plugin_bundle.py</code> | Sync/check source to plugin bundle |
| <code>rhino7-native-probe-result.json</code> / <code>rhino7-visible-check-result.json</code> | Fixed-example live Rhino 7 records |
| <code>LICENSE.txt</code> | Repository MIT license text |
| <code>LICENSE</code> | Apache License, Version 2.0 for SoDam AI Studio authored additions |
| <code>NOTICE.md</code> | Upstream attribution, adaptation, and pre-publication rights checks |

Architecture: project source → bundle build → local marketplace registration → installed Codex skill cache → Codex code response → human applies code to Rhino 7 component. The answer alone does not change or save a Rhino document. The root <code>README.html</code> is a user guide, not a required input to the installed skill.

<a id="en-9"></a>
### 9. Security and data flow

- Local Python <code>run</code>, <code>emit</code>, detector, and XML lookup commands read project inputs or installed Rhino files and return local results. This repository has no application login screen, DB, web server, or MCP server of its own.
- Text you send to Codex, and relevant files Codex reads, **may be processed by the Codex service**. Do not put private drawings, customer names, API keys, Rhino license keys, or passwords into prompts, custom rules, or sample JSON. Review the [OpenAI privacy policy](https://openai.com/policies/privacy-policy/) for your account context.
- <code>references/custom-rules.md</code> is persistent local text in the project or installed copy. Do not put secrets there; review it before sharing.
- <code>README.html</code> has no external script, remote image, or account login. Clicking its source links opens the named websites.
- Rhino 7 component code runs against the **current Rhino/Grasshopper document data**. Review newly generated code for file/network effects before use and test important models on a copy.
- The repository's MIT license does not grant rights to Rhino or Codex. Follow each product's normal account and license rules.

<a id="en-10"></a>
### 10. Evidence and troubleshooting

**Observed locally on 2026-09-27:** local marketplace plugin installed/enabled; fresh Codex session explicitly loaded the skill; the installed copy ran the independent bounds sample; five **fixed** Rhino 7 Grasshopper examples passed: C# division/bounds, GhPython division/bounds, and C# Brep Tree. Visible canvas records show no warnings/errors and Rhino object count 67 before/after. See the [acceptance matrix](references/parity-matrix.md) and both JSON records. Arbitrary new nodes, native Rhino 8, and installation on another PC remain **unverified**.

| Symptom | Check | Action |
| --- | --- | --- |
| <code>codex</code> not found | <code>codex --version</code> | Check official CLI installation, PATH, and login; open a new PowerShell window. |
| <code>py -3.12</code> not found | <code>py --list</code> | Install 3.12 or use the exact command for an installed Python **3.10+**. |
| Marketplace/plugin install fails | Current directory, both JSON manifests, bundle <code>--check</code> | Run from project root and read the actual error. Do not delete global Codex settings. |
| Generic Rhino 8 answer after install | <code>codex plugin list</code>; <code>$sodam-rhinoghcode</code> and <code>Rhino 7</code> in prompt | Start a new chat with explicit skill, version, and C#/GhPython target. |
| Rhino 7 startup or license error | Rhino's own message and license/account state | Restore normal startup with McNeel support. Offline calculations are not proof of native Rhino execution. |
| Grasshopper will not open | Rhino <code>_Grasshopper</code> command output | Check Rhino installation and Grasshopper component. Save existing work, then use a new test document. |
| Red/orange node or no result | Runtime messages, compile error, names/types/Item-List-Tree, paste location | Copy the error and compare with the [Rhino 7 port guide](references/rhino7-component-guide.md). For C#, paste only the body; check output initialization and idle input. |
| Independent input fails | JSON shape, points, finite numbers, segment count | Copy a sample JSON and alter one field at a time. See [input limits](references/offline-compatibility.md). |
| Old answers after update | Difference between project source and installed cache | Rebuild/check/reinstall the plugin and start a new chat; back up custom rules. |

<a id="en-11"></a>
### 11. FAQ

**Q. Does installing this add a button in Rhino?**

A. No. It adds a Codex skill. Use existing Rhino 7 C# Script/GhPython nodes.

**Q. Can I use this without a Rhino license?**

A. Codex code generation and two independent point calculations do not launch Rhino. **Native Rhino 7/Grasshopper execution requires normal Rhino usage rights.** This project does not bypass them.

**Q. Can I paste Python 3 into Rhino 7 GhPython?**

A. Do not assume compatibility. Request Rhino 7 GhPython/IronPython 2.7 or legacy C# Script.

**Q. Does pasting code create ports automatically?**

A. No. Set Rhino 7 ports manually in the component UI according to the returned table.

**Q. Has every generated script been tested?**

A. No. Five fixed examples passed live Rhino 7 checks. Verify each new script's normal, idle, invalid-input, and output behavior.

**Q. Does offline calculation replace Grasshopper?**

A. No. It performs only open-polyline division and point bounds.

**Q. Can I use it offline?**

A. The HTML guide and two local Python calculations can be read/run offline. Codex chat, installation, and account connectivity depend on your environment.

**Q. How do I share it with another PC or workplace?**

A. Transfer the project folder with license notices; recheck plugin installation and Rhino 7 execution there. Check workplace Codex plugin policy. Public marketplace publication is a separate process.

<a id="en-12"></a>
### 12. License, copyright, and commercial use

- **Basic terms:** Material inherited from [DariyXYZ/grasshopper-script-nodes](https://github.com/DariyXYZ/grasshopper-script-nodes) remains under the MIT terms in [LICENSE.txt](LICENSE.txt). Additions authored by SoDam AI Studio are under the **Apache License, Version 2.0** in [LICENSE](LICENSE). Retain applicable notices from both and include [NOTICE.md](NOTICE.md) when distributing the combined project. MIT permits use, modification, copying, forking, redistribution, and sale, subject to retaining its original copyright and permission notices. [MIT text](https://opensource.org/license/mit) · [Apache 2.0 text](https://www.apache.org/licenses/LICENSE-2.0).
- **In plain language:** You may use the project for personal work, company work, teaching, paid services, or client delivery if you follow the applicable license terms. Keep the relevant MIT and Apache 2.0 notices when modifying, copying, forking, redistributing, or selling the project itself. **These permissions cover only material within each license's scope.** Check separate rights for third-party code, drawings, models, images, fonts, icons, video, audio, templates, and data.
- **Check separately:** Verify valid Rhino/Grasshopper usage rights and version terms; Codex account and plugin rules; external API/model/SDK/service terms and fees; the source, commercial use rights, and possible similarity or infringement of AI-generated code, docs, images, and outputs; and client delivery rights. See [McNeel licensing](https://www.rhino3d.com/en/features/administration/select-licensing-method/). The repository has no package dependency manifest, but rights to external products such as Rhino and Codex are not included.
- **Do not:** Redistribute without applicable MIT and Apache notices, bypass Rhino license terms, or publish/deliver third-party trademarks, logos, works, personal information, client material, private documents, or API secrets without permission. The names Rhino, Grasshopper, and Codex describe compatibility; they do not imply official status or endorsement by their owners. Generated outputs are not automatically rights-cleared.
- **Source and publication scope:** Upstream `LICENSE.txt` says `Copyright (c) 2026` without a rights-holder name; none has been invented. The upstream `install-flow-report.md` contains a real user path and is excluded from the new public repository, as are two screenshots pending rights review. `install-report-sample.md` is an older Rhino 8 example, not proof of current installation. Exact upstream/contributor notices and adaptation rights **require legal or specialist review**.
- **Warranty and liability:** MIT provides the software “AS IS,” without warranty. Correctness, structural safety, noninfringement, and commercial results are not guaranteed. Construction, fabrication, and client delivery geometry require separate professional review.

General information only; no legal effect is guaranteed. The user remains responsible and should consult qualified legal counsel.

<a id="en-13"></a>
### 13. Sources

- [Upstream project](https://github.com/DariyXYZ/grasshopper-script-nodes) · [MIT license text](https://opensource.org/license/mit)
- [OpenAI Codex](https://developers.openai.com/codex/) · [Plugin overview](https://help.openai.com/en/articles/20001256-plugins-in-codex/)
- [McNeel Rhino downloads](https://www.rhino3d.com/en/download/) · [Rhino license methods](https://www.rhino3d.com/en/features/administration/select-licensing-method/)
- [McNeel Rhino.Python](https://developer.rhino3d.com/guides/rhinopython/what-is-rhinopython/) · [Rhino C# component](https://developer.rhino3d.com/guides/grasshopper/csharp-essentials/1-grasshopper-csharp-component/)
