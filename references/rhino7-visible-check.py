"""Inspect the displayed Rhino 7 Grasshopper test canvas and fit it in view."""
import json
import os
import traceback

import Rhino


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'rhino7-visible-check-result.json')


def main():
    result = {'status': 'fail'}
    try:
        import Grasshopper
        from Grasshopper.Kernel import GH_RuntimeMessageLevel
        from System.Drawing import PointF
        canvas = Grasshopper.Instances.ActiveCanvas
        doc = canvas.Document if canvas is not None else None
        object_count = len(list(doc.Objects)) if doc is not None else 0
        if object_count != 12:
            raise RuntimeError('Expected 12 test canvas objects; found %s' % object_count)
        doc.NewSolution(True)
        cases = []
        for obj in doc.Objects:
            name = str(obj.NickName)
            if name not in ('csharp-divide_polyline', 'csharp-bounds_points',
                            'ironpython-divide_polyline', 'ironpython-bounds_points',
                            'csharp-brep-tree'):
                continue
            errors = [str(x) for x in obj.RuntimeMessages(GH_RuntimeMessageLevel.Error)]
            warnings = [str(x) for x in obj.RuntimeMessages(GH_RuntimeMessageLevel.Warning)]
            if name == 'csharp-brep-tree':
                data = obj.Params.Output[1].VolatileData
                paths = [str(x) for x in data.Paths]
                counts = [branch.Count for branch in data.Branches]
                passed = paths == ['{0}', '{1}', '{2}'] and counts == [1, 2, 1]
                case = {'name': name, 'paths': paths, 'branch_counts': counts}
            else:
                outputs = []
                number = 1 if name.endswith('divide_polyline') else 2
                for index in range(number):
                    output = obj.Params.Output[index + 1]
                    outputs.extend([[float(p.Value.X), float(p.Value.Y), float(p.Value.Z)]
                                    for p in output.VolatileData.AllData(True)])
                expected = ([[0, 0, 0], [2, 0, 0], [2, 2, 0], [2, 4, 0]]
                            if name.endswith('divide_polyline') else
                            [[-1, -2, -5], [4, 8, 6]])
                passed = outputs == expected
                case = {'name': name, 'actual': outputs, 'expected': expected}
            case['errors'] = errors
            case['warnings'] = warnings
            case['pass'] = passed and not errors and not warnings
            cases.append(case)
        if len(cases) != 5:
            raise RuntimeError('Expected five script components')
        canvas.Viewport.Zoom = 0.45
        canvas.Viewport.MidPoint = PointF(790, 650)
        canvas.Refresh()
        result = {'status': 'pass' if all(x['pass'] for x in cases) else 'fail',
                  'cases': cases, 'rhino_object_count': Rhino.RhinoDoc.ActiveDoc.Objects.Count,
                  'visible_canvas': bool(Grasshopper.Instances.DocumentEditor.Visible)}
    except Exception:
        result['error'] = traceback.format_exc()
    with open(REPORT, 'w') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True))
    Rhino.RhinoApp.WriteLine('Visible check result: ' + REPORT)
    Rhino.RhinoApp.WriteLine('Visible check status: ' + result['status'])


if __name__ == '__main__':
    main()
