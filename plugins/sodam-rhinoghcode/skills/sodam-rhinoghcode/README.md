# SoDam-RhinoGHCode

English-only guide: [README.en.md](README.en.md).

> Rhino 7 Grasshopper 스크립트 노드용 **Codex 로컬 마켓플레이스 플러그인**. 한국어 안내가 먼저 나오고, 같은 내용을 영어로 이어서 제공합니다. 이 저장소는 Rhino에 설치하는 .gha 파일이 아닙니다.

**이 문서의 기준:** 2026-09-27에 확인한 프로젝트 파일과 로컬 시험 기록. 공개 소스 주소는 [sodam-ai/SoDam-RhinoGHCode](https://github.com/sodam-ai/SoDam-RhinoGHCode)입니다. 설치 명령은 다운로드한 프로젝트 폴더 안에서 실행합니다.

## 한국어

### 목차

1. [무엇을 하는 도구인가요?](#ko-1)
2. [준비물과 다운로드](#ko-2)
3. [마켓플레이스 플러그인 설치](#ko-3)
4. [5분 빠른 시작](#ko-4)
5. [실행·사용·작동 방식](#ko-5)
6. [명령어 모음](#ko-6)
7. [업데이트 요약](#ko-7)
8. [파일 위치와 아키텍처](#ko-8)
9. [보안과 데이터 흐름](#ko-9)
10. [검증 범위와 오류 대처](#ko-10)
11. [자주 묻는 질문](#ko-11)
12. [라이선스·저작권·상업적 사용](#ko-12)
13. [공식 자료](#ko-13)
14. [English guide](#en-guide)

<a id="ko-1"></a>
### 1. 무엇을 하는 도구인가요?

Grasshopper는 Rhino 안에서 노드를 연결해 형상을 만드는 도구입니다. **스크립트 노드**는 그중 코드를 붙여 넣는 상자입니다. 이 플러그인은 Codex에게 “내 Rhino 버전에 맞는 노드 코드와 포트 설정을 써 달라”고 요청할 때 쓰는 지침과 도구를 묶었습니다.

- **Rhino 7 중심:** 기존 C# Script 노드의 <code>RunScript</code> 본문 또는 GhPython의 IronPython 2.7 코드, 입력·출력 포트 이름·자료형·Item/List/Tree 접근 방식·기본값·설명을 제공합니다. 포트는 Rhino 7 화면에서 직접 설정합니다.
- **Rhino 8 안내 유지:** C# <code>GH_ScriptInstance</code>, Python 3 또는 IronPython 2 요청을 구분합니다. 이 컴퓨터에서 Rhino 8 실제 노드 실행은 확인하지 않았습니다.
- **보조 계산:** 점 목록의 같은 길이 폴리라인 분할과 3D 경계값 계산은 Rhino 없이 Python 표준 라이브러리로 실행할 수 있습니다. 이 계산 결과는 Grasshopper 실행 증거가 아닙니다.
- **정체:** Codex **플러그인 안의 스킬**입니다. Rhino용 .gha 파일, 자동으로 Rhino 화면을 조작하는 앱, 라이선스 인증 우회 도구가 아닙니다.

<a id="ko-2"></a>
### 2. 준비물과 다운로드

| 목적 | 필요한 것 | 구하는 방법 |
| --- | --- | --- |
| Codex에서 코드 생성 | 이 프로젝트 폴더, 플러그인 명령을 지원하는 Codex 데스크톱/CLI, Codex에 접속 가능한 계정 | [Codex 공식 안내](https://developers.openai.com/codex/)에서 설치·로그인 안내를 따릅니다. PowerShell에서 <code>codex --version</code>과 <code>codex plugin --help</code>로 명령이 보이는지 확인합니다. |
| 플러그인 묶음 생성과 선택적 보조 계산 | Python 3.10 이상; 이 프로젝트의 검증 기준은 3.12 | [Python 공식 다운로드](https://www.python.org/downloads/windows/)에서 Windows 설치 파일을 받습니다. 설치 후 <code>py -3.12 --version</code>으로 확인합니다. 3.10 이상이면 <code>python</code> 명령도 사용할 수 있으나 설치된 버전을 확인하세요. |
| 실제 Rhino 7 노드 실행 | 정상 실행되는 Rhino 7, 해당 제품에 유효한 라이선스, 포함된 Grasshopper | [McNeel 다운로드/이전 버전](https://www.rhino3d.com/en/download/)에서 정식 경로를 확인합니다. 이미 설치했다면 다시 다운로드할 필요가 없습니다. |
| 문서 읽기 | Markdown 뷰어 또는 웹 브라우저 | <code>README.md</code>를 Codex/편집기에서 열거나 <code>README.html</code>을 브라우저에서 엽니다. HTML은 인터넷 없이도 본문을 읽을 수 있습니다. |

**프로젝트 파일 받기:** [이 프로젝트의 GitHub 페이지](https://github.com/sodam-ai/SoDam-RhinoGHCode)에서 초록색 **Code → Download ZIP**을 누르고 압축을 풀어도 됩니다. Git을 설치했다면 아래 `git clone` 명령을 사용할 수 있습니다. [DariyXYZ의 원본 저장소](https://github.com/DariyXYZ/grasshopper-script-nodes)는 기반 프로젝트이며 Rhino 7용 SoDam 개작본의 다운로드 주소가 아닙니다.

PowerShell 열기: Windows 시작 메뉴에서 “PowerShell”을 검색합니다. 아래 명령은 각 줄을 붙여 넣고 Enter를 누릅니다. 경로에 공백이 있을 수 있으므로 따옴표를 지우지 마세요. 프로젝트 폴더 안의 파일을 실행하기 전에 출처를 확인하세요.

<a id="ko-3"></a>
### 3. 마켓플레이스 플러그인 설치

**이미 이 컴퓨터에 설치한 경우:** 2026-09-27 로컬 확인에서는 <code>sodam-rhinoghcode@sodam-rhinoghcode</code>가 installed/enabled로 표시됐습니다. 먼저 <code>codex plugin list</code>로 현재 상태를 확인하고, 그대로 있으면 4번으로 가세요.

처음 설치하거나 프로젝트 소스 변경을 설치본에 반영할 때:

~~~powershell
git clone https://github.com/sodam-ai/SoDam-RhinoGHCode.git
Set-Location -LiteralPath '.\SoDam-RhinoGHCode'
py -3.12 -B scripts/build_plugin_bundle.py
py -3.12 -B scripts/build_plugin_bundle.py --check
codex plugin marketplace add .
codex plugin add sodam-rhinoghcode@sodam-rhinoghcode
codex plugin list
~~~

1. 첫 줄은 프로젝트를 받으며, 두 번째 줄은 그 폴더로 이동합니다. ZIP을 받았다면 이 두 줄 대신 압축을 푼 폴더에서 PowerShell을 열고 세 번째 줄부터 실행합니다.
2. 세 번째 줄은 프로젝트 스킬을 플러그인 묶음에 반영합니다. 네 번째 줄의 <code>--check</code>가 실패하면 설치 전에 오류를 해결합니다.
3. 다섯 번째 줄의 마침표(<code>.</code>)는 **현재 폴더를 로컬 마켓플레이스로 등록**한다는 뜻입니다. 공개 웹 마켓플레이스에 올리는 명령이 아닙니다.
4. 여섯 번째 줄은 그 마켓플레이스의 플러그인을 Codex에 설치합니다. 마지막 줄에서 정확한 ID와 활성 상태를 확인합니다. 표시되지 않으면 아래 문제 해결을 봅니다.
5. 새 Codex 채팅을 열어 <code>$sodam-rhinoghcode</code>를 요청 맨 앞에 적습니다. 기존 채팅에 방금 설치한 스킬이 바로 보이지 않으면 새 채팅 또는 Codex 재시작을 사용합니다.

이 플러그인에는 별도 MCP 서버·API 키·플러그인 전용 Rhino 인증이 없습니다. **실제 Rhino 7 실행에는 Rhino의 정상적인 라이선스가 필요합니다.** Codex 계정 접근 조건도 별개입니다.

<a id="ko-4"></a>
### 4. 5분 빠른 시작

1. Codex를 열고 새 채팅에 다음 문장을 보냅니다.

   > $sodam-rhinoghcode Rhino 7 Grasshopper GhPython 노드로 점 목록의 경계값을 계산해줘. 입력·출력 포트 이름, Point3d 타입 힌트, List/Item 접근 방식, 코드를 붙여 넣을 위치, 빈 입력 결과도 알려줘.

2. 답변에 **Rhino 7 / GhPython / IronPython 2.7**이 적혀 있는지 확인합니다. Rhino 8 Python 3/SDK 코드를 Rhino 7에 붙여 넣지 마세요.
3. Rhino 7을 정상 실행한 다음 명령줄에 <code>_Grasshopper</code>를 입력합니다. 새 Grasshopper 문서에 **GhPython** 노드를 놓습니다.
4. 답변의 포트 표에 따라 입력·출력 이름, 타입 힌트, 접근 방식을 **노드 화면에서** 맞춥니다. 코드는 GhPython 편집기에 붙여 넣습니다. 답변의 코드만 붙여서는 포트 설정이 자동으로 바뀌지 않습니다.
5. 작은 점 목록을 연결해 값과 경고를 확인하고, 입력을 뺐을 때 출력이 비워지는지 확인합니다. 저장은 사용자가 원하는 Grasshopper 문서에 합니다. 기존 Rhino 모델을 시험 대상으로 쓰기 전에 사본을 저장하세요.

C#을 원하면 요청에서 <code>GhPython</code>을 <code>C# Script</code>로 바꾸고, 답변의 **RunScript 본문**만 기존 Rhino 7 C# 편집기의 그 메서드 안에 넣습니다. 독립 계산용 JSON <code>code</code> 필드는 이스케이프된 문자열이므로 직접 붙여 넣기 전에 아래 6번의 디코딩 명령을 사용합니다.

<a id="ko-5"></a>
### 5. 실행·사용·작동 방식

**전체 흐름:** 요청에 Rhino 버전과 노드 종류를 적음 → Codex가 설치된 스킬·기본 규칙·사용자 규칙·주의 목록을 읽음 → 필요하면 로컬 Rhino 설치 정보와 <code>RhinoCommon.xml</code>을 조회함 → 버전에 맞는 코드와 수동 포트 표를 답함 → 사용자가 Rhino 7 Grasshopper 노드에 적용하고 실제 입력으로 확인함.

더 구체적인 요청 예시:

- <code>$sodam-rhinoghcode Rhino 7 C# Script에서 Brep 면의 선을 Tree로 출력해줘. B/F/N 입력의 타입·접근 방식과 빈 입력 동작을 알려줘.</code>
- <code>$sodam-rhinoghcode Rhino 7 GhPython 노드를 만들어줘. 입력이 연결되지 않으면 출력은 빈 목록으로 유지해줘.</code>
- <code>$sodam-rhinoghcode Rhino 8 Python 3 Script 코드를 작성해줘.</code> — Rhino 8 실행은 이 컴퓨터에서 미검증입니다.

<code>$sodam-rhinoghcode</code>를 명시하세요. 단순히 “Grasshopper 코드”라고만 쓰면 다른 스킬이 선택되거나 이 스킬이 읽히지 않을 수 있습니다. **새로 생성한 모든 노드는 따로 실행 확인**해야 합니다. 이미 통과한 예제 5건이 새 코드의 성공을 보장하지는 않습니다.

<a id="ko-6"></a>
### 6. 명령어 모음

모든 명령은 프로젝트 최상위 폴더의 PowerShell에서 실행합니다. <code>python</code>이 3.10 이상으로 연결된 환경이라면 <code>py -3.12</code> 대신 <code>python</code>을 쓸 수 있습니다.

| 하고 싶은 일 | 명령 |
| --- | --- |
| Codex 설치 상태 보기 | <code>codex plugin list</code> |
| 현재 소스와 플러그인 묶음 일치 확인 | <code>py -3.12 -B scripts/build_plugin_bundle.py --check</code> |
| Rhino 7 설치 정보 보기 | <code>py -3.12 -B scripts/detect_rhino_environment.py --rhino-major 7 --pretty</code> |
| Rhino 7 API 문서 항목 조회 | <code>py -3.12 -B scripts/lookup_rhinocommon_docs.py --rhino-major 7 --member Surface.IsoCurve --pretty</code> |
| 점 목록 폴리라인 분할 계산 | <code>py -3.12 -B scripts/offline_node.py run offline-polyline-sample.json</code> |
| 점 목록 3D 경계값 계산 | <code>py -3.12 -B scripts/offline_node.py run offline-bounds-sample.json</code> |
| Rhino 7 C# 노드 코드와 포트 표 출력 | <code>py -3.12 -B scripts/offline_node.py emit --operation bounds_points --language csharp</code> |
| Rhino 7 GhPython 노드 코드와 포트 표 출력 | <code>py -3.12 -B scripts/offline_node.py emit --operation bounds_points --language ironpython</code> |
| 전체 로컬 도구 점검 | <code>py -3.12 -B scripts/verify_tooling.py --rhino-major 7</code> |

분할용 코드에는 <code>--operation divide_polyline</code>을 사용합니다. <code>emit</code> 결과는 JSON입니다. 해당 <code>code</code> 필드를 사람이 붙여 넣을 수 있는 문자열로 복사하려면:

~~~powershell
py -3.12 -B scripts/offline_node.py emit --operation bounds_points --language ironpython |
  ConvertFrom-Json | Select-Object -ExpandProperty code | Set-Clipboard
~~~

클립보드 복사는 **현재 클립보드 내용을 교체**합니다. 원래 내용이 중요하면 먼저 다른 곳에 보관하세요. 지원되지 않는 operation/language나 잘못된 JSON 입력은 오류로 처리됩니다. 독립 계산은 점 목록의 두 연산만 지원하며 RhinoCommon 전체를 실행하지 않습니다. 자세한 입력 규칙은 [독립 계산 범위](references/offline-compatibility.md)를 보세요.

<a id="ko-7"></a>
### 7. 업데이트 요약

<details>
<summary>펼쳐서 보기: 현재 구현과 변경 내용</summary>
<p><strong>Rhino 7 대응:</strong> 원본의 Rhino 8 중심 설명을 Rhino 7 구형 C# Script와 GhPython/IronPython 2.7의 코드 위치·포트 수동 설정에 맞춰 보강했습니다. Rhino 8 지침은 남아 있습니다.</p>
<p><strong>Codex 설치:</strong> 로컬 <code>.agents/plugins/marketplace.json</code>, 플러그인 매니페스트, <code>sodam-rhinoghcode</code> 스킬 묶음을 추가했습니다. 원본의 별도 스킬 설치 방식도 보조 경로로 남아 있지만 이 문서는 마켓플레이스 경로를 기준으로 합니다.</p>
<p><strong>검증:</strong> 점 계산 두 종류와 대응 C#/GhPython 네 노드, C# Brep Tree 한 노드가 실제 Rhino 7 Grasshopper의 고정 시험에서 통과했습니다. 빈 입력 시험과 문서 정리도 포함됩니다. Rhino 8 및 임의의 새 노드 전체 통과를 뜻하지 않습니다.</p>
<p><strong>이 README:</strong> 초보자용 한·영 사용법, 로컬 설치, 데이터 흐름, 저작권과 상업적 사용 범위를 추가하고 동일 본문의 HTML을 생성했습니다. 이 요약은 날짜별 전체 Git 변경 이력이 아닙니다.</p>
</details>

소스 문서를 바꾼 뒤에는 <code>build_plugin_bundle.py</code>를 실행하고 <code>--check</code>를 통과시킨 다음 <code>codex plugin add sodam-rhinoghcode@sodam-rhinoghcode</code>로 설치본을 새로 고칩니다. 다시 <code>codex plugin list</code>를 확인하고 **새 채팅**에서 호출합니다. 개인 규칙 <code>references/custom-rules.md</code>을 사용한다면 변경 전 사본을 보관하고 충돌 내용을 확인하세요. 마켓플레이스 설치본과 원본 프로젝트 폴더는 서로 다른 복사본입니다.

<a id="ko-8"></a>
### 8. 파일 위치와 아키텍처

| 프로젝트 상대 위치 | 역할 |
| --- | --- |
| <code>README.md</code> / <code>README.html</code> | 이 문서의 같은 내용, Markdown / 브라우저용 HTML |
| <code>.agents/plugins/marketplace.json</code> | 로컬 마켓플레이스 목록 |
| <code>plugins/sodam-rhinoghcode/.codex-plugin/plugin.json</code> | 플러그인 이름·버전·스킬 위치 |
| <code>plugins/sodam-rhinoghcode/skills/sodam-rhinoghcode/</code> | Codex가 설치하는 스킬 묶음 |
| <code>SKILL.md</code> | 스킬의 주된 작업 지침 |
| <code>references/rhino7-component-guide.md</code> | Rhino 7 포트와 붙여 넣기 위치 |
| <code>references/parity-matrix.md</code> | 원본 대비 구현·증거·남은 한계 |
| <code>references/custom-rules.md</code> | 사용자가 추가하는 개인 생성 규칙 |
| <code>scripts/offline_node.py</code> | 두 점 목록 연산과 Rhino 7 코드 출력 |
| <code>scripts/build_plugin_bundle.py</code> | 스킬 소스와 설치용 묶음 동기화·검사 |
| <code>rhino7-native-probe-result.json</code> / <code>rhino7-visible-check-result.json</code> | 고정 예제의 실제 Rhino 7 시험 기록 |
| <code>LICENSE.txt</code> | 이 저장소의 MIT 라이선스 전문 |
| <code>LICENSE</code> | SoDam AI Studio가 작성한 추가 부분에 적용하는 Apache License, Version 2.0 전문 |
| <code>NOTICE.md</code> | 원본 출처, 개작 사실, 공개 전 권리 확인 사항 |

**구조:** 프로젝트 소스 → 묶음 생성 → 로컬 마켓플레이스 등록 → Codex 설치 캐시의 스킬 → Codex의 코드 답변 → 사람이 Rhino 7 노드에 적용. Codex 답변만으로 Rhino 문서가 변경되거나 3D 형상이 자동 저장되지는 않습니다. <code>README.html</code>은 최상위 사용자 문서이며 플러그인 스킬 묶음의 필수 입력은 아닙니다.

<a id="ko-9"></a>
### 9. 보안과 데이터 흐름

- 로컬 Python 명령 <code>run</code>, <code>emit</code>, 버전 감지, XML 조회는 프로젝트 입력 파일이나 설치된 Rhino 파일을 읽고 계산/출력을 만듭니다. 이 코드에 자체 로그인 화면, DB, 웹 서버, MCP 서버는 없습니다.
- Codex 채팅에서 **사용자가 입력한 요청과 Codex가 읽은 관련 파일 내용**은 사용 중인 Codex 서비스의 처리 범위에 들어갈 수 있습니다. 그러므로 비공개 도면, 고객 이름, API 키, Rhino 라이선스 키, 암호를 요청·규칙·샘플 JSON에 넣지 마세요. Codex의 계정·데이터 정책은 [공식 안내](https://openai.com/policies/privacy-policy/)에서 따로 확인합니다.
- <code>references/custom-rules.md</code>는 프로젝트 또는 설치 복사본에 남는 로컬 텍스트입니다. 개인 정보나 비밀을 쓰지 말고, 공개 공유 전 반드시 검토합니다.
- 브라우저용 <code>README.html</code>은 외부 스크립트·원격 이미지·계정 로그인을 사용하지 않습니다. 본문의 공식 문서 링크는 클릭할 때 브라우저가 해당 사이트로 이동합니다.
- Rhino 7 노드 실행은 **열린 Rhino/Grasshopper 문서의 현재 데이터**를 사용합니다. 생성 코드가 임의의 파일·네트워크 작업을 추가하지 않았는지 사용 전 확인하고, 중요한 모델은 별도 사본으로 시험합니다.
- 이 프로젝트의 MIT 라이선스는 Rhino나 Codex의 사용 권한을 주지 않습니다. 권한 문제를 피하려면 각 제품의 정상 설치·계정·라이선스를 따릅니다.

<a id="ko-10"></a>
### 10. 검증 범위와 오류 대처

**확인된 기록:** 2026-09-27 이 컴퓨터에서 로컬 마켓플레이스 플러그인 installed/enabled, 새 Codex 세션의 명시적 스킬 호출, 설치본의 독립 경계값 계산, 실제 Rhino 7 Grasshopper의 **고정 노드 5건**을 확인했습니다. 5건은 C# 분할/경계값, GhPython 분할/경계값, C# Brep Tree입니다. 화면 시험 기록에는 다섯 건 모두 경고·오류가 없고 Rhino 객체 수가 시험 전후 67개입니다. [시험 범위표](references/parity-matrix.md)와 두 JSON 결과 파일을 보세요. **임의의 새 노드, Rhino 8 실제 실행, 다른 PC 설치는 미확인**입니다.

| 증상 | 먼저 확인할 것 | 다음 조치 |
| --- | --- | --- |
| <code>codex</code> 명령을 못 찾음 | <code>codex --version</code> | Codex CLI 설치·PATH·로그인을 공식 안내대로 확인한 뒤 새 PowerShell 창을 엽니다. |
| <code>py -3.12</code>를 못 찾음 | <code>py --list</code> | Python 3.12를 설치하거나 이미 있는 **3.10 이상**의 정확한 실행 명령을 사용합니다. |
| 마켓플레이스 등록/플러그인 설치 실패 | 현재 위치, 두 JSON 매니페스트, <code>build_plugin_bundle.py --check</code> | 프로젝트 최상위에서 다시 실행하고 나온 오류 문구를 읽습니다. 임의로 전역 Codex 설정을 지우지 마세요. |
| 설치됐는데 응답이 일반적인 Rhino 8 코드 | <code>codex plugin list</code>, 요청의 <code>$sodam-rhinoghcode</code>와 <code>Rhino 7</code> | 새 채팅에서 정확한 스킬 이름·버전을 명시하고 Rhino 7 C#/GhPython으로 다시 요청합니다. |
| Rhino 7이 안 열림/라이선스 오류 | Rhino 자체의 오류 창·계정·라이선스 상태 | McNeel 공식 라이선스 지원으로 정상 실행 문제를 해결합니다. 보조 계산 성공을 Rhino 실행 성공으로 해석하지 마세요. |
| Grasshopper 명령이 안 열림 | Rhino 명령줄의 <code>_Grasshopper</code> 출력 | Rhino 설치와 Grasshopper 구성 요소를 점검합니다. 기존 문서를 먼저 저장하고 새 테스트 문서에서 확인합니다. |
| 노드가 빨강/주황, 출력 없음 | 런타임 메시지, C# 컴파일 오류, 포트 이름/타입/Item·List·Tree, 코드 붙인 위치 | 오류 문구를 복사하고 [Rhino 7 포트 가이드](references/rhino7-component-guide.md)와 대조합니다. C#은 <code>RunScript</code> 본문만 넣고 출력 초기화·빈 입력을 확인합니다. |
| 독립 계산 입력 오류 | JSON 형식·점 좌표·유한 숫자·분할 수 | 예제 JSON을 복사해 한 항목씩 수정합니다. 검증 제한과 지원 연산을 [범위 문서](references/offline-compatibility.md)에서 확인합니다. |
| 업데이트했는데 옛 답변 | 프로젝트 소스와 설치 캐시의 차이 | 묶음 생성·검사 후 플러그인을 다시 설치하고 새 채팅에서 호출합니다. 사용자 규칙은 별도로 백업합니다. |

<a id="ko-11"></a>
### 11. 자주 묻는 질문

**Q. 설치하면 Rhino에 새 버튼이 생기나요?**

A. 아니요. Codex에 스킬이 추가됩니다. Rhino 7에는 기존 C# Script/GhPython 노드를 사용합니다.

**Q. Rhino 라이선스 없이 이 플러그인을 쓸 수 있나요?**

A. Codex에서 코드 생성과 두 독립 점 계산은 Rhino를 시작하지 않습니다. **실제 Rhino 7·Grasshopper 실행은 정상적인 Rhino 사용 권한이 있어야 합니다.** 라이선스 문제를 우회하지 않습니다.

**Q. Python 3 코드를 Rhino 7 GhPython에 넣어도 되나요?**

A. 권장하지 않습니다. Rhino 7 요청은 GhPython/IronPython 2.7 또는 구형 C# Script로 명시하세요.

**Q. 코드만 붙이면 포트도 자동으로 생기나요?**

A. Rhino 7에서는 포트를 노드 UI에서 직접 추가·설정해야 합니다. 답변의 표를 그대로 따라야 합니다.

**Q. 모든 생성 코드가 이미 테스트됐나요?**

A. 아니요. 고정 예제 5건만 실제 Rhino 7에서 확인됐습니다. 새 작업의 입력·빈 입력·오류·출력을 그 작업의 노드에서 확인해야 합니다.

**Q. 오프라인 계산은 모든 Grasshopper 기능을 대체하나요?**

A. 아니요. 점 목록의 폴리라인 분할과 경계값 두 연산만 수행합니다.

**Q. 인터넷 없이 쓸 수 있나요?**

A. HTML 문서와 두 로컬 Python 계산은 오프라인에서 읽거나 실행할 수 있습니다. Codex 채팅·설치·계정 접근의 온라인 요구는 사용 환경에 따릅니다.

**Q. 다른 PC나 회사에 공유하려면?**

A. 프로젝트 폴더와 라이선스 고지를 함께 전달하고 그 PC에서 설치·Rhino 7 실행을 다시 확인합니다. 회사 Codex 계정의 플러그인 허용 정책도 확인하세요. 공개 마켓플레이스 등록은 별도 절차입니다.

<a id="ko-12"></a>
### 12. 라이선스·저작권·상업적 사용

- **기본 조건:** 원본 [DariyXYZ/grasshopper-script-nodes](https://github.com/DariyXYZ/grasshopper-script-nodes)에서 계승한 부분은 [LICENSE.txt](LICENSE.txt)의 MIT 조건을 따릅니다. SoDam AI Studio가 새로 작성한 추가 부분에는 [LICENSE](LICENSE)의 **Apache License, Version 2.0**을 적용합니다. 둘을 포함한 배포에는 해당하는 고지를 모두 보존하고 [NOTICE.md](NOTICE.md)를 함께 전달하세요. MIT는 사용·수정·복제·포크·재배포·판매를 허용하지만 원본 저작권·허가문 보존을 요구합니다. [MIT 원문](https://opensource.org/license/mit) · [Apache 2.0 원문](https://www.apache.org/licenses/LICENSE-2.0).
- **쉽게 말해:** 해당 라이선스 조건을 지키면 개인 작업, 회사 업무, 교육 자료, 유료 서비스나 고객 납품에 활용할 수 있습니다. 프로젝트 자체를 수정·복제·포크·재배포·판매할 때도 MIT와 Apache 2.0의 해당 고지를 유지해야 합니다. **이 허용은 각 라이선스의 적용 범위에 한정**됩니다. 다른 사람의 코드·도면·모델·이미지·폰트·아이콘·영상·음원·템플릿·데이터는 별도 권리를 확인하세요.
- **별도로 확인할 것:** Rhino/Grasshopper의 유효한 사용 권한과 버전 약관, Codex 계정·플러그인 정책, 외부 API/모델/SDK/서비스의 이용 약관과 요금제, 입력 자료와 AI 생성 코드·문서·이미지·결과물의 출처·상업적 이용·유사 저작물 침해 가능성, 고객 납품 권한을 확인하세요. [McNeel 라이선스 안내](https://www.rhino3d.com/en/features/administration/select-licensing-method/). 이 저장소에는 패키지 의존성 명세가 없지만, Rhino와 Codex 같은 외부 제품의 권리는 포함되지 않습니다.
- **하면 안 되는 것:** 적용되는 MIT·Apache 고지를 제거한 채 재배포하거나, Rhino 라이선스 조건을 우회하거나, 제3자의 상표·로고·저작물·개인정보·고객 자료·비공개 문서·API 비밀값을 허락 없이 공개·납품하지 마세요. Rhino·Grasshopper·Codex라는 이름은 호환 대상 설명이며 해당 회사의 공식 제품·제휴를 뜻하지 않습니다. 생성 결과물은 자동으로 권리가 확보되지 않습니다.
- **출처와 공개 범위:** 원본 `LICENSE.txt`의 저작권 줄은 `Copyright (c) 2026`만 있고 권리자 이름은 없습니다. 이를 임의로 채우지 않았습니다. 원본의 `install-flow-report.md`에 실제 사용자 경로가 있어 새 공개 저장소에서 제외하며, 화면 캡처 2개도 권리 확인 전까지 제외합니다. `install-report-sample.md`는 Rhino 8의 과거 예시이지 현재 설치 증거가 아닙니다. 원본·기여자의 정확한 고지와 개작분의 권리 범위는 **법무/전문가 검토 필요**입니다.
- **보증과 책임:** MIT 전문의 “AS IS” 조항에 따라 보증이 없습니다. 코드 정확성, 구조 안전, 법적 비침해나 상업적 성과를 보장하지 않습니다. 실제 시공·제작·납품 형상은 별도 전문 검토가 필요합니다.

이 항목은 일반 안내입니다. **참고용·법적 효력 보장 안 함, 사용자 책임·변호사 확인 권장.**

<a id="ko-13"></a>
### 13. 공식 자료

- [원본 프로젝트](https://github.com/DariyXYZ/grasshopper-script-nodes) · [MIT 라이선스 원문](https://opensource.org/license/mit)
- [OpenAI Codex 안내](https://developers.openai.com/codex/) · [플러그인 개요](https://help.openai.com/en/articles/20001256-plugins-in-codex/)
- [McNeel Rhino 다운로드](https://www.rhino3d.com/en/download/) · [Rhino 라이선스 방식](https://www.rhino3d.com/en/features/administration/select-licensing-method/)
- [McNeel Rhino.Python 안내](https://developer.rhino3d.com/guides/rhinopython/what-is-rhinopython/) · [Rhino 7 C# 컴포넌트](https://developer.rhino3d.com/guides/grasshopper/csharp-essentials/1-grasshopper-csharp-component/)

---

<a id="en-guide"></a>
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
