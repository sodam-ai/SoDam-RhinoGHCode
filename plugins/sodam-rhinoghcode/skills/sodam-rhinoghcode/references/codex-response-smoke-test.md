# Local Codex response smoke test, 2026-09-27

## Installed-skill follow-up after user authorization

The user approved allowing a new ephemeral Codex CLI session to read the installed global skill and its references. The first new Brep Tree response included the required `using Grasshopper;` and empty-path initialization, but used `B.PathCount` on `DataTree<Brep>`. Compiling the entire answer with `verify_rhino7_csharp_api.py --source-file` failed with CS1061. The source and installed skill now instruct use of `BranchCount`, `Path(i)`, and `Branch(i)` for `DataTree<T>` inputs.

A second new installed-skill response used those APIs and its complete source compiled against the installed Rhino 7 and Grasshopper DLLs (`status: pass`, `cases: ["provided_source"]`). Its code returns when auxiliary face-index tree `F` is null before it creates output paths from `B`, despite promising to preserve every input path. This is a behavioral failure found by inspecting control flow; compilation cannot catch it. The source and installed skill now require creating promised paths before auxiliary-input early returns.

A third explicit installed-skill response placed `EnsurePath(B.Path(i))` before the return for missing `F` or invalid `N`. Its complete C# source compiled against installed Rhino 7 DLLs (`status: pass`, `cases: ["provided_source"]`). This verifies that specific answer's syntax and path-preservation control-flow order, not its native component output. Its port table omitted individual input/output tooltip descriptions, so the complete-response gate remains partial.

In a fresh Codex CLI session, a generic Rhino 7 Grasshopper C# request did not read the installed skill (`SkillReadEvidence` was empty). The response wrongly assigned `Curve.DivideByCount(N, true)` to `Point3d[]`; the installed Rhino 7 method returns `double[]`. The session log reported skills-context-budget overflow with 1072 additional skills omitted. In another fresh session, the prompt `Use the grasshopper-script-nodes skill` caused Codex to read the installed `SKILL.md` and return `double[]` with `PointAt(t)` conversion. Therefore explicit skill naming is verified; automatic selection is not working in the observed CLI session.

The initial five sessions ran from `D:\AI_Dev_Work\2026y\26y_09m_30d_SoDam` with
`codex exec --ephemeral -s read-only -C <project> <prompt>` on Codex CLI
`0.156.1` with model `gpt-5.6-terra`. Each prompt explicitly requested the
local `SKILL.md`. This verifies instruction-following only: no user-level skill
installation, automatic discovery, Rhino launch or Grasshopper canvas run was
observed. The text below records the final answers, excluding CLI diagnostics
and hook messages. Later cases are appended below with their own conditions.

## Case 1: C# before the count-input rule

Prompt:

> Read the local SKILL.md and follow it. Generate a Rhino 7 legacy Grasshopper C# Script component that divides one connected Curve into 5 equal segments and outputs the points. Include only the RunScript method body and a complete component input/output setup table, safe behavior when Curve is disconnected, and the exact Rhino 7 Curve.DivideByCount return type with local XML evidence. Do not edit files. Answer in Korean.

Final answer:

> [페르소나: L2 · 3D 모델링 전문가 관점]
>
> ```csharp
> Pts = new System.Collections.Generic.List<Rhino.Geometry.Point3d>();
>
> if (C == null || !C.IsValid || C.GetLength() <= Rhino.RhinoMath.ZeroTolerance)
>   return;
>
> double[] parameters = C.DivideByCount(5, true);
> if (parameters == null)
>   return;
>
> var points = new System.Collections.Generic.List<Rhino.Geometry.Point3d>(parameters.Length);
> foreach (double t in parameters)
>   points.Add(C.PointAt(t));
>
> Pts = points;
> ```
>
> | 방향 | 이름 | Type hint | Access | 기본값 | 설명 |
> |---|---|---|---|---|---|
> | Input | `C` | `Curve` | `Item` | 없음 | 하나의 유효한 연결 Curve. 미연결 시 빈 목록 출력. |
> | Output | `Pts` | `Point3d` | List | 해당 없음 | 5개 등길이 구간의 분할점. 양 끝점을 포함하여 보통 6점 출력. |
>
> 기본 `out` 출력은 제거하세요. 컴포넌트 설명: `Divide one valid curve into 5 equal-length segments and output the endpoints.`
>
> 정확한 Rhino 7 반환 타입은 `double[]`입니다: `Double[] DivideByCount(Int32, Boolean)`. 로컬 XML의 `Curve.DivideByCount(Int32, Boolean)` 항목은 성공 시 “분할점의 curve parameters”, 실패 시 `null`을 반환한다고 명시합니다. 따라서 각 `double` 파라미터를 `C.PointAt(t)`로 점으로 변환합니다. XML 의미와 설치 DLL 리플렉션으로 대조했으며, 실제 Grasshopper 캔버스 실행은 미검증입니다.

Assessment: correct target and return semantics; `Pts` is initialized, but
the sample count was hardcoded and the reusable `N` input was omitted.

## Case 2: GhPython

Prompt:

> Read the local SKILL.md and its mandatory references. Generate a Rhino 7 GhPython IronPython 2.7 component that divides a connected Curve into N equal segments, default N=5, returning division points. Give a whole script body and complete manual port setup table including type hint, access, default, and descriptions. Disconnected Curve must return an empty result. Use the Rhino 7 Curve.DivideByCount return semantics. Do not edit files or run tests or claim local execution. Answer briefly in Korean.

Final answer:

> [페르소나: L2 · 3D 모델링 관점]
>
> `Curve.DivideByCount(N, True)`는 점이 아닌 매개변수 배열을 반환하므로 `PointAt()`으로 변환합니다. 연결되지 않은 `C` 입력은 빈 목록입니다.
>
> ```python
> # Rhino 7 GhPython / IronPython 2.7 전체 스크립트 본문
> Pts = []
>
> if C is not None and C.IsValid:
>     if N is None:
>         N = 5
>
>     if N > 0:
>         parameters = C.DivideByCount(N, True)
>         if parameters is not None:
>             Pts = [C.PointAt(t) for t in parameters]
> ```
>
> | 포트 | 방향 | 타입 힌트 | 접근 | 기본값 | 설명 |
> |---|---|---|---|---|---|
> | `C` | 입력 | Curve | Item | 없음 | 등분할할 단일 유효 곡선. 미연결 시 빈 결과 |
> | `N` | 입력 | Integer | Item | Persistent `5` | 곡선을 나눌 동일 길이 세그먼트 수 |
> | `Pts` | 출력 | Point | List | — | 양 끝점을 포함한 분할점들 (`N + 1`개) |
>
> GhPython 출력 포트를 `Pts`로 이름 변경하고 기본 `out`은 제거하세요. 실행이나 테스트는 하지 않았고, 파일도 변경하지 않았습니다.

Assessment: Rhino 7-compatible script text, configurable `N`, complete input
settings and empty disconnected result. Output port type/access labels were
written as descriptions, not verified as editable legacy output settings.

## Case 3: C# after the count-input rule

Prompt:

> Read local SKILL.md and mandatory references. For Rhino 7 legacy C# Script, generate a node dividing an input Curve into 5 equal segments and outputting points. Treat 5 as the initial suggested count, not an explicitly fixed count. Provide the RunScript body and complete manual port setup. Do not edit files, run tests, or claim execution. Answer briefly in Korean.

Final answer:

> [페르소나: L2 · 3D 모델링 전문가]
>
> Rhino 7 **C# Script** 노드의 기존 `RunScript` 안에 아래 본문만 붙여넣으세요.
>
> ```csharp
> Pts = new List<Point3d>();
>
> if (C == null || N < 1) return;
>
> double[] parameters = C.DivideByCount(N, true);
> if (parameters == null) return;
>
> List<Point3d> points = new List<Point3d>();
> foreach (double t in parameters)
>   points.Add(C.PointAt(t));
>
> Pts = points;
> ```
>
> 포트 설정:
>
> | 구분 | 이름 | 타입/접근 | 기본값 | 설명 |
> |---|---|---|---|---|
> | 입력 | `C` | Curve / Item | 없음 | 등분할할 곡선 |
> | 입력 | `N` | Integer / Item | 영구값 `5` | 등분할할 세그먼트 수 |
> | 출력 | `Pts` | Point 목록 | — | 끝점을 포함한 분할점 |
>
> 기본 `out` 출력은 제거하세요. 코드 편집기 imports에 없다면 `System.Collections.Generic`, `Rhino.Geometry`를 추가합니다. `N=5`는 초기 제안값일 뿐, 입력 포트에서 자유롭게 바꿀 수 있습니다. 로컬 API 문서상 `DivideByCount`는 점이 아닌 파라미터를 반환하므로 `PointAt`으로 점 변환했습니다. 실행·테스트는 하지 않았습니다.

Assessment: this revised response includes `N` with persistent default 5,
idle-safe output and a Rhino 7 legacy `RunScript` body. This prompt also
explicitly clarified that 5 was a suggested count, so it cannot isolate the
effect of the skill edit. The generated body was not compiled or run.

## Case 4: identical original C# prompt after the first count-input rule

Prompt: exactly the same text as Case 1.

Final answer:

> [페르소나: L2 · 3D 모델링 관점]
>
> **RunScript 메서드 본문**
> (레거시 C# Script의 자동 생성된 `RunScript` 내부에만 붙여넣기)
>
> ```csharp
> Pts = new List<Point3d>();
>
> if (C == null) return;
>
> double[] parameters = C.DivideByCount(5, true);
> if (parameters == null) return;
>
> foreach (double t in parameters)
>   Pts.Add(C.PointAt(t));
> ```
>
> | 구분 | 이름 | 접근 | 형식 힌트 | 기본값/설명 |
> |---|---|---:|---|---|
> | 입력 | `C` | Item | Curve | 분할할 연결된 곡선 |
> | 출력 | `Pts` | List | Point3d | 5개 등길이 구간의 분할점 6개(양 끝점 포함) |
>
> `C`가 연결되지 않았거나 비어 있으면 `Pts`는 빈 `List<Point3d>`로 유지되고 오류 없이 종료됩니다. `System.Collections.Generic`, `Rhino.Geometry` import가 필요합니다.
>
> 반환형은 정확히 `double[]`입니다. 로컬 Rhino 7 XML의 `M:Rhino.Geometry.Curve.DivideByCount(System.Int32,System.Boolean)`은 “성공 시 분할점의 curve parameters 목록, 실패 시 null”을 명시합니다. 로컬 `RhinoCommon.dll` IL 메타데이터도 해당 메서드를 `instance float64[]`로 표시하므로, 반환값은 점 배열이 아니라 매개변수 `double[]`이며 `C.PointAt(t)`로 점으로 변환해야 합니다. 로컬 문서 조회는 성공했지만, Grasshopper 캔버스에서의 실제 실행은 수행하지 않았습니다.

Assessment: fail. The same prompt still produced a hardcoded count and no `N`
port. More seriously, `Pts` is `ref object` in the legacy signature, so
`Pts.Add(...)` is a compile-time error; a minimal compiler check returned
`CS1061`. The rule and guide were strengthened after this finding.

## Case 5: identical original C# prompt after the stronger rule

Prompt: exactly the same text as Cases 1 and 4.

Final answer:

> [페르소나: L2 · 3D 모델링 전문가]
>
> | 구분 | 이름 | 형식/접근 | 기본값 | 설명 |
> |---|---|---|---|---|
> | 입력 | `C` | `Curve` / Item | 없음, 선택 입력 | 하나의 유효한 연결 곡선 |
> | 입력 | `N` | `Integer` / Item | 영구값 `5` | 동일 길이로 나눌 세그먼트 수 |
> | 출력 | `Pts` | Point3d 목록 | — | 분할 매개변수를 실제 점으로 변환한 결과 |
> | 출력 | `out` | 제거 | — | 진단 출력이 필요 없으므로 제거 |
>
> ```csharp
> Pts = new System.Collections.Generic.List<Rhino.Geometry.Point3d>();
>
> // C 포트가 연결되지 않았거나 유효하지 않으면 빈 목록을 유지한다.
> if (C == null || !C.IsValid || N < 1)
>   return;
>
> double[] parameters = C.DivideByCount(N, true);
> if (parameters == null)
>   return;
>
> var points = new System.Collections.Generic.List<Rhino.Geometry.Point3d>();
> foreach (double t in parameters)
>   points.Add(C.PointAt(t));
>
> Pts = points;
> ```
>
> 확인됨: Rhino 7의 `Curve.DivideByCount(int, bool)` 정확한 반환 형식은 `double[]` (`System.Double[]`)입니다. 로컬 XML `C:\Program Files\Rhino 7\System\RhinoCommon.xml`의 해당 멤버는 반환값을 “성공 시 분할점의 curve parameters 목록, 실패 시 `null`”로 명시합니다. 따라서 `Point3d[]`로 직접 받지 않고 `C.PointAt(t)`로 변환합니다. Grasshopper 캔버스에서의 실제 실행은 검증하지 않았습니다.

Assessment: the identical prompt now returned a configurable `N` port, a
typed local collection and an idle-safe `ref object` assignment. Its method
body compiled with the Windows .NET Framework C# compiler against the
installed Rhino 7 `RhinoCommon.dll`, in a wrapper with `Curve C`, `int N` and
`ref object Pts`. This confirms syntax and referenced API signatures, not
Grasshopper UI wiring or execution.

## Tooling context

The first read-only Codex session attempted `verify_tooling.py`, whose tests
create temporary files. Its sandbox rejected those writes, so the reported
tooling failure is specific to that test environment. Running
`python -B scripts/verify_tooling.py --rhino-major 7` outside the nested
read-only sandbox passed 27 tests with one platform skip, including C# compile
and installed IronPython stub execution. Other globally configured skills hit a
scan limit or missing frontmatter, and unrelated external MCP servers returned
authentication errors. None prevented the five final responses; they remain
ambient environment issues rather than Rhino 7 acceptance evidence.

## Case 6: Rhino 7 trimmed Brep isocurves

Prompt: Read the local SKILL.md and mandatory references. Generate a Rhino 7 legacy C# Script node for a trimmed Brep face: input Brep B, face index F, and N=3 interior constant-U isocurve locations; preserve visible trims; return all curve fragments grouped by sample location. Give the RunScript body, any helper method separately, and exact manual port settings. Check local Rhino 7 RhinoCommon.xml for BrepFace.TrimAwareIsoCurve direction and return shape. Explain face orientation, seams and boundaries, and do not claim native execution. Do not edit files. Answer in Korean.

Final answer:

> [페르소나: L2 · 3D 모델링 관점]
>
> ## 1. 결과
>
> 권장 방식은 `BrepFace.TrimAwareIsoCurve(0, u)`입니다. `direction = 0`은 **U 값이 일정한 곡선**이며, 트림을 반영해 `Curve[]` 조각들을 반환합니다. 각 U 샘플의 조각은 출력 트리의 한 브랜치에 보존됩니다.
>
> ## 2. RunScript 본문
>
> 레거시 C# Script 편집기가 만든 `RunScript(Brep B, int F, int N, ref object C)` 내부에 아래 본문만 붙여 넣으세요.
>
> ```csharp
> var curvesBySample = new DataTree<Curve>();
> C = curvesBySample;
>
> if (B == null)
>   return;
>
> if (!B.IsValid)
> {
>   Print("B is not a valid Brep.");
>   return;
> }
>
> if (F < 0 || F >= B.Faces.Count)
> {
>   Print("F is outside the Brep face-index range.");
>   return;
> }
>
> if (N < 1)
> {
>   Print("N must be at least 1.");
>   return;
> }
>
> BrepFace face = B.Faces[F];
> Interval uDomain = face.Domain(0);
>
> if (!uDomain.IsValid)
> {
>   Print("The selected face has no valid U domain.");
>   return;
> }
>
> for (int i = 0; i < N; i++)
> {
>   // N=3이면 U 도메인의 1/4, 2/4, 3/4 지점만 사용한다.
>   double u = InteriorParameter(uDomain, i + 1, N);
>
>   // Rhino 7: direction 0 = constant-U isocurve.
>   Curve[] fragments = face.TrimAwareIsoCurve(0, u);
>   if (fragments == null)
>     continue;
>
>   GH_Path path = new GH_Path(i);
>
>   foreach (Curve fragment in fragments)
>   {
>     if (fragment != null && fragment.IsValid)
>       curvesBySample.Add(fragment, path);
>   }
> }
>
> C = curvesBySample;
> ```
>
> ## 3. 별도 Helper method
>
> 스크립트 편집기의 Additional Code 영역에 넣으세요.
>
> ```csharp
> private static double InteriorParameter(Interval domain, int oneBasedIndex, int count)
> {
>   double normalized = (double) oneBasedIndex / (count + 1);
>   return domain.T0 + normalized * (domain.T1 - domain.T0);
> }
> ```
>
> 추가 `using`:
>
> ```csharp
> using Rhino.Geometry;
> using Grasshopper.Kernel.Data;
> ```
>
> ## 4. 수동 포트 설정
>
> | 포트 | 방향 | Type hint | Access | 기본값 | 설명 |
> |---|---|---|---|---|---|
> | `B` | Input | `Brep` | Item | 없음 | 트림이 유지되어야 하는 Brep |
> | `F` | Input | `int` | Item | `0` | 사용할 face의 0부터 시작하는 인덱스 |
> | `N` | Input | `int` | Item | `3` | 경계를 제외한 constant-U 샘플 수 |
> | `C` | Output | `Curve` | Tree | — | 샘플 위치별 트림 반영 curve fragments |
> | `out` | Output | 기본 유지 | Item | — | 최초 검증 시 컴파일/런타임 진단용 |
>
> `N = 3`이면 `face.Domain(0)`의 정규화된 U 위치 `0.25`, `0.50`, `0.75`가 각각 `{0}`, `{1}`, `{2}` 브랜치가 됩니다. 각 브랜치 안에는 해당 위치에서 나온 모든 트림 조각이 들어갑니다.
>
> ## 5. 확인된 API 의미
>
> 로컬 [`RhinoCommon.xml`](C:\Program Files\Rhino 7\System\RhinoCommon.xml:12936)에서 확인했습니다.
>
> - `TrimAwareIsoCurve(0, constantParameter)`의 `0`은 **constant U**입니다.
> - `1`은 constant V입니다.
> - 트림을 고려하며 여러 curve를 반환할 수 있습니다.
> - 로컬 `RhinoCommon.dll` 메타데이터 반사 확인 결과 반환형은 정확히 `Rhino.Geometry.Curve[]`입니다.
>
> ## 6. 방향·심·경계 주의
>
> - `OrientationIsReversed`는 Brep face의 방향이 원래 surface 방향과 반대임을 뜻합니다. 이 코드는 UV 매개변수 기준으로 constant-U 곡선을 얻을 뿐이므로, 이 플래그 때문에 U/V를 바꾸거나 curve를 임의로 뒤집지 않습니다. 이후 법선, 오프셋, 한쪽 방향 처리가 필요할 때만 별도로 반영하세요.
> - 주기 surface의 seam은 U 도메인 양 끝과 연결될 수 있습니다. 이 코드는 끝값을 제외하므로 seam 자체를 샘플하지는 않지만, seam 인접 형상에서 조각의 공간적 중복 여부를 자동 병합·제거하지는 않습니다.
> - 경계 curve는 별도로 출력하지 않습니다. 다만 각 내부 isocurve의 끝은 보이는 trim 경계에서 끊기므로, 구멍이나 불규칙한 trim도 조각 형태로 보존됩니다.
> - 트림 밖에 해당 U 위치가 전혀 없으면 그 브랜치는 비어 있을 수 있습니다. 이는 오류가 아니라 해당 constant-U 선이 보이는 face 영역을 통과하지 않는 경우입니다.
>
> ## 7. 검증 상태
>
> 파일 변경은 하지 않았습니다. Rhino 7 로컬 XML과 DLL 메타데이터는 확인했지만, 현재 Grasshopper 네이티브 런타임에서 이 코드를 붙여 넣고 실행·시각 검수한 것은 아닙니다. 따라서 실제 노드 실행은 미검증 상태입니다. `B` 없음, 유효하지 않은 `F`, `N < 1`, 구멍이 있는 trimmed face를 순서대로 시험해 보세요.

Assessment: exact installed Rhino 7 XML and DLL agree that direction 0 means constant U and TrimAwareIsoCurve returns Curve[]. The response selected trimmed BrepFace and grouped fragments, but its listed imports omitted `using Grasshopper;`; compilation with the stated imports and Rhino 7 RhinoCommon.dll, Grasshopper.dll and GH_IO.dll failed with CS0246 for DataTree. Adding that import made the same wrapper compile. The response also claimed empty sample branches, yet the body only added paths when a valid fragment existed. Rhino 7 Grasshopper.dll reflection confirmed DataTree<T>.EnsurePath(GH_Path). The skill and Rhino 7 guide were strengthened. Native canvas execution remains unverified.
