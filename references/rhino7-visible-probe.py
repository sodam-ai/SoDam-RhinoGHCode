"""Show the five already validated Rhino 7 script nodes on an isolated GH canvas."""
import imp
import json
import os
import traceback

import Rhino


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'rhino7-visible-probe-result.json')
CORE = imp.load_source('rhino7_native_probe', os.path.join(
    ROOT, 'references', 'rhino7-native-probe.py'))


def _panel(doc, source, x, y):
    from Grasshopper.Kernel.Special import GH_Panel
    from System.Drawing import PointF
    panel = GH_Panel()
    panel.CreateAttributes()
    panel.Attributes.Pivot = PointF(x, y)
    doc.AddObject(panel, False)
    panel.AddSource(source)
    return panel


def main():
    report = {'status': 'fail'}
    doc = None
    shown = False
    try:
        import Grasshopper
        from Grasshopper.Kernel import GH_Document
        from Grasshopper.Kernel.Types import GH_Brep, GH_Point
        from Rhino.Geometry import Brep, Circle, Curve, Interval, Plane, Point3d, Rectangle3d
        from System import Array
        from System.Drawing import PointF

        server = Grasshopper.Instances.DocumentServer
        canvas = Grasshopper.Instances.ActiveCanvas
        if canvas is None or canvas.Document is not None or server.DocumentCount != 0:
            raise RuntimeError('Visible test requires an empty Grasshopper canvas')
        if Rhino.RhinoApp.Version.Major != 7:
            raise RuntimeError('Rhino 7 is required')
        before = Rhino.RhinoDoc.ActiveDoc.Objects.Count
        with open(CORE.MANIFEST, 'r') as stream:
            manifest = json.load(stream)
        doc = GH_Document()
        doc.Enabled = True
        results = []
        for row, language in enumerate(('csharp', 'ironpython')):
            for col, operation in enumerate(('divide_polyline', 'bounds_points')):
                result = CORE._run_case(doc, language, operation,
                                        manifest[language][operation])
                if not result['connected']['pass'] or not result['idle']['pass']:
                    raise RuntimeError('Native case failed: %s/%s' % (language, operation))
                component = list(doc.Objects)[-1]
                component.Attributes.Pivot = PointF(240 + col * 750, 180 + row * 450)
                values = ([(0, 0, 0), (2, 0, 0), (2, 4, 0)]
                          if operation == 'divide_polyline'
                          else [(4, -2, 6), (-1, 8, 3), (2, 0, -5)])
                for coords in values:
                    component.Params.Input[0].PersistentData.Append(
                        GH_Point(Point3d(*coords)))
                for index in range(1 if operation == 'divide_polyline' else 2):
                    _panel(doc, component.Params.Output[index + 1],
                           570 + col * 750, 180 + row * 450 + index * 130)
                results.append(result)

        result = CORE._run_tree_case(doc, manifest['brep_tree'])
        if not result['connected']['pass'] or not result['idle']['pass']:
            raise RuntimeError('Native Brep Tree case failed')
        tree_component = list(doc.Objects)[-1]
        tree_component.Attributes.Pivot = PointF(240, 1080)
        outer = Rectangle3d(Plane.WorldXY, Interval(0, 10), Interval(0, 10)).ToNurbsCurve()
        inner = Circle(Plane.WorldXY, Point3d(5, 5, 0), 2).ToNurbsCurve()
        breps = Brep.CreatePlanarBreps(Array[Curve]([outer, inner]), 0.01)
        valid = next((b for b in breps if b is not None and b.IsValid
                      and b.Faces.Count == 1 and b.Faces[0].Loops.Count > 1), None)
        if valid is None:
            raise RuntimeError('Trimmed Brep fixture could not be recreated')
        tree_component.Params.Input[0].SetPersistentData(GH_Brep(valid))
        _panel(doc, tree_component.Params.Output[1], 570, 1080)
        results.append(result)

        doc.NewSolution(True)
        after = Rhino.RhinoDoc.ActiveDoc.Objects.Count
        if after != before:
            raise RuntimeError('Rhino model object count changed: %s to %s'
                               % (before, after))
        server.AddDocument(doc)
        canvas.Document = doc
        shown = True
        report = {'status': 'pass', 'rhino_version': str(Rhino.RhinoApp.Version),
                  'rhino_objects_before': before, 'rhino_objects_after': after,
                  'case_count': len(results), 'panel_count': 7,
                  'active_canvas': canvas.Document is doc,
                  'document_count': server.DocumentCount}
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if doc is not None and not shown:
            doc.Dispose()
        with open(REPORT, 'w') as stream:
            stream.write(json.dumps(report, indent=2, sort_keys=True))
        Rhino.RhinoApp.WriteLine('Visible probe result: ' + REPORT)
        Rhino.RhinoApp.WriteLine('Visible probe status: ' + report['status'])


if __name__ == '__main__':
    main()
