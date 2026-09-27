# Run once from Rhino 7 with _-RunPythonScript. This creates a detached
# Grasshopper document; it does not add objects to Rhino or the visible canvas.
import clr
import json
import os
import traceback

import Rhino

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'references', 'rhino7-native-probe.json')
REPORT = os.path.join(ROOT, 'rhino7-native-probe-result.json')


def _points(values):
    return [[float(p.X), float(p.Y), float(p.Z)] for p in values]


def _near(actual, expected):
    if len(actual) != len(expected):
        return False
    for a, e in zip(actual, expected):
        if any(abs(x - y) > 1e-6 for x, y in zip(a, e)):
            return False
    return True


def _write_report(report):
    with open(REPORT, 'w') as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True))
    Rhino.RhinoApp.WriteLine('Native probe result: ' + REPORT)
    Rhino.RhinoApp.WriteLine('Native probe status: ' + report['status'])


def _all_data(param):
    return [goo.Value for goo in param.VolatileData.AllData(True)]


def _diagnostic_data(component):
    return [str(goo) for goo in component.Params.Output[0].VolatileData.AllData(True)]


def _messages(component, level):
    return [str(item) for item in component.RuntimeMessages(level)]


def _run_case(doc, language, operation, code):
    from Grasshopper.Kernel import GH_ParamAccess, GH_RuntimeMessageLevel
    from Grasshopper.Kernel.Parameters.Hints import GH_IntegerHint_CS, GH_Point3dHint
    from Grasshopper.Kernel.Types import GH_Integer, GH_Point
    from Rhino.Geometry import Point3d

    if language == 'csharp':
        from ScriptComponents import Component_CSNET_Script
        component = Component_CSNET_Script()
    else:
        from GhPython.Component import ZuiPythonComponent
        component = ZuiPythonComponent()

    component.NickName = language + '-' + operation
    component.CreateAttributes()
    p = component.Params.Input[0]
    p.Name = 'P'
    p.NickName = 'P'
    p.Description = 'Probe points'
    p.Access = GH_ParamAccess.list
    p.TypeHint = GH_Point3dHint()
    p.Optional = True

    if operation == 'divide_polyline':
        n = component.Params.Input[1]
        n.Name = 'N'
        n.NickName = 'N'
        n.Access = GH_ParamAccess.item
        n.TypeHint = GH_IntegerHint_CS()
        n.Optional = True
        n.SetPersistentData(GH_Integer(3))
        output_names = ['Pts']
    else:
        # The second stock input is unused for this one-input operation.
        component.Params.Input[1].Optional = True
        output_names = ['Min', 'Max']
        from Grasshopper.Kernel.Parameters import Param_GenericObject
        extra = Param_GenericObject()
        extra.Name = 'Max'
        extra.NickName = 'Max'
        component.Params.RegisterOutputParam(extra)

    for index, name in enumerate(output_names):
        output = component.Params.Output[index + 1]  # stock 'out' is diagnostic
        output.Name = name
        output.NickName = name
    component.Params.OnParametersChanged()

    if language == 'csharp':
        # Rhino 7's legacy component already supplies these imports. Adding
        # them again emits CS0105 warnings. None triggers a solve exception.
        component.ScriptSource.UsingCode = ''
        component.ScriptSource.ScriptCode = code
    else:
        component.Code = code

    if operation == 'divide_polyline':
        coords = [(0, 0, 0), (2, 0, 0), (2, 4, 0)]
        expected = [[0, 0, 0], [2, 0, 0], [2, 2, 0], [2, 4, 0]]
    else:
        coords = [(4, -2, 6), (-1, 8, 3), (2, 0, -5)]
        expected = [[-1, -2, -5], [4, 8, 6]]
    for xyz in coords:
        p.PersistentData.Append(GH_Point(Point3d(*xyz)))
    doc.AddObject(component, False)
    doc.NewSolution(True)

    observed = []
    for index in range(len(output_names)):
        observed.extend(_points(_all_data(component.Params.Output[index + 1])))
    errors = _messages(component, GH_RuntimeMessageLevel.Error)
    warnings = _messages(component, GH_RuntimeMessageLevel.Warning)
    diagnostics = _diagnostic_data(component)
    run_count = component.RunCount
    connected_pass = _near(observed, expected) and not errors and not warnings

    p.Script_ClearPersistentData()
    component.ExpireSolution(False)
    doc.NewSolution(True)
    idle = [len(_all_data(component.Params.Output[i + 1]))
            for i in range(len(output_names))]
    idle_errors = _messages(component, GH_RuntimeMessageLevel.Error)
    idle_warnings = _messages(component, GH_RuntimeMessageLevel.Warning)
    idle_pass = all(count == 0 for count in idle) and not idle_errors and not idle_warnings

    result = {'language': language, 'operation': operation,
              'connected': {'pass': connected_pass, 'actual': observed,
                            'expected': expected, 'errors': errors, 'warnings': warnings,
                            'diagnostics': diagnostics, 'run_count': run_count},
              'idle': {'pass': idle_pass, 'output_counts': idle,
                       'errors': idle_errors, 'warnings': idle_warnings}}
    return result


def _run_tree_case(doc, code):
    from Grasshopper.Kernel import GH_ParamAccess, GH_RuntimeMessageLevel
    from Grasshopper.Kernel.Parameters import Param_ScriptVariable
    from Grasshopper.Kernel.Parameters.Hints import GH_BrepHint, GH_IntegerHint_CS
    from Grasshopper.Kernel.Types import GH_Brep, GH_Integer
    from Rhino.Geometry import Brep, Circle, Curve, Interval, Plane, Point3d, Rectangle3d
    from System import Array
    from ScriptComponents import Component_CSNET_Script

    component = Component_CSNET_Script()
    component.NickName = 'csharp-brep-tree'
    component.CreateAttributes()
    b = component.Params.Input[0]
    b.Name = b.NickName = 'B'
    b.TypeHint = GH_BrepHint()
    b.Access = GH_ParamAccess.item
    b.Optional = True
    f = component.Params.Input[1]
    f.Name = f.NickName = 'F'
    f.TypeHint = GH_IntegerHint_CS()
    f.Access = GH_ParamAccess.item
    f.Optional = True
    f.SetPersistentData(GH_Integer(0))
    n = Param_ScriptVariable()
    n.Name = n.NickName = 'N'
    n.TypeHint = GH_IntegerHint_CS()
    n.Access = GH_ParamAccess.item
    n.Optional = True
    n.SetPersistentData(GH_Integer(3))
    component.Params.RegisterInputParam(n)
    component.Params.Output[1].Name = 'C'
    component.Params.Output[1].NickName = 'C'
    component.Params.OnParametersChanged()
    component.ScriptSource.UsingCode = ''
    component.ScriptSource.ScriptCode = code

    outer = Rectangle3d(Plane.WorldXY, Interval(0, 10), Interval(0, 10)).ToNurbsCurve()
    inner = Circle(Plane.WorldXY, Point3d(5, 5, 0), 2).ToNurbsCurve()
    candidates = Brep.CreatePlanarBreps(Array[Curve]([outer, inner]), 0.01)
    brep = next((x for x in candidates if x is not None and x.IsValid
                 and x.Faces.Count == 1 and x.Faces[0].Loops.Count > 1), None)
    if brep is None:
        return {'operation': 'brep_tree', 'pass': False,
                'error': 'No valid planar face with an inner trim was created'}
    b.SetPersistentData(GH_Brep(brep))
    doc.AddObject(component, False)
    doc.NewSolution(True)
    data = component.Params.Output[1].VolatileData
    paths = [str(path) for path in data.Paths]
    counts = [branch.Count for branch in data.Branches]
    errors = _messages(component, GH_RuntimeMessageLevel.Error)
    warnings = _messages(component, GH_RuntimeMessageLevel.Warning)
    diagnostics = _diagnostic_data(component)
    run_count = component.RunCount
    connected_pass = (paths == ['{0}', '{1}', '{2}'] and
                      any(count >= 2 for count in counts) and not errors and not warnings)

    b.Script_ClearPersistentData()
    component.ExpireSolution(False)
    doc.NewSolution(True)
    idle_paths = [str(path) for path in component.Params.Output[1].VolatileData.Paths]
    idle_errors = _messages(component, GH_RuntimeMessageLevel.Error)
    idle_warnings = _messages(component, GH_RuntimeMessageLevel.Warning)
    idle_pass = not idle_paths and not idle_errors and not idle_warnings
    return {'operation': 'brep_tree', 'connected': {
        'pass': connected_pass, 'paths': paths, 'branch_counts': counts,
        'errors': errors, 'warnings': warnings,
        'diagnostics': diagnostics, 'run_count': run_count},
        'idle': {'pass': idle_pass, 'paths': idle_paths,
                 'errors': idle_errors, 'warnings': idle_warnings}}


def main():
    report = {'status': 'fail', 'scope': 'native Rhino 7 Grasshopper script components',
              'cases': []}
    doc = None
    try:
        if Rhino.RhinoApp.Version.Major != 7:
            raise RuntimeError('Rhino 7 required; active Rhino major is %s'
                               % Rhino.RhinoApp.Version.Major)
        from Grasshopper.Kernel import GH_Document
        rhino_system = os.path.dirname(clr.GetClrType(Rhino.RhinoApp).Assembly.Location)
        components = os.path.abspath(os.path.join(
            rhino_system, '..', 'Plug-ins', 'Grasshopper', 'Components'))
        clr.AddReferenceToFileAndPath(
            os.path.join(components, 'ScriptComponents.gha'))
        clr.AddReferenceToFileAndPath(
            os.path.join(components, 'GhPython.gha'))
        with open(MANIFEST, 'r') as stream:
            manifest = json.load(stream)
        doc = GH_Document()
        doc.Enabled = True
        report['document_state'] = {'enabled': doc.Enabled,
                                    'enable_solutions': GH_Document.EnableSolutions}
        if not GH_Document.EnableSolutions:
            raise RuntimeError('Grasshopper solutions are disabled in the current session')
        for language in ('csharp', 'ironpython'):
            for operation in ('divide_polyline', 'bounds_points'):
                try:
                    report['cases'].append(_run_case(
                        doc, language, operation, manifest[language][operation]))
                except Exception:
                    report['cases'].append({'language': language,
                                            'operation': operation, 'pass': False,
                                            'error': traceback.format_exc()})
        try:
            report['cases'].append(_run_tree_case(doc, manifest['brep_tree']))
        except Exception:
            report['cases'].append({'operation': 'brep_tree', 'pass': False,
                                    'error': traceback.format_exc()})
        report['rhino_version'] = str(Rhino.RhinoApp.Version)
        report['status'] = ('pass' if all(
            case.get('connected', {}).get('pass') and case.get('idle', {}).get('pass')
            for case in report['cases']) else 'fail')
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if doc is not None:
            doc.Dispose()
    _write_report(report)


if __name__ == '__main__':
    main()
