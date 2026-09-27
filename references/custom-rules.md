# Custom Grasshopper Rules

This file stores user-specific persistent preferences gathered during real work.

Priority:

1. Explicit request in the current conversation
2. Rules in this file
3. `references/default-rules.md`

Update method:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_python.ps1 .\scripts\update_custom_rules.py --rule "<rule text>" --source "user conversation"
```

## Rules

- 2026-04-13 - Source: user conversation 2026-04-13
  When creating a new Grasshopper script node, assign practical non-zero default values to numeric and toggle inputs whenever it is safe, so connecting geometry immediately produces a visible result for quick testing. Do not invent geometry; only prefill example parameter values.
- 2026-04-13 - Source: user conversation 2026-04-13
  When creating a new Grasshopper script node, provide clear descriptions for the node and for each input and output so the hover text explains the logic without needing to read the code. Prefer practical natural-language tooltips that describe the effect of each parameter.

### 2026-06-30 11:06 UTC

- Source: user conversation 2026-06-30
- Rule: For Grasshopper C# RhinoCommon scripts, do not treat Plane.FitPlaneToPoints as returning bool. In RhinoCommon it returns PlaneFitResult; compare the result to PlaneFitResult.Success, or for three known non-collinear triangle vertices use new Plane(A, B, C) and check plane.IsValid. This prevents CS0023/CS0023-like errors such as Operator '!' cannot be applied to operand of type 'PlaneFitResult'.
