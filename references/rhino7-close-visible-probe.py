"""Close only the isolated Grasshopper test definition without a save prompt."""
import json
import os
import traceback

import Rhino


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'rhino7-visible-cleanup-result.json')
NAMES = set(('csharp-divide_polyline', 'csharp-bounds_points',
             'ironpython-divide_polyline', 'ironpython-bounds_points',
             'csharp-brep-tree'))


def main():
    result = {'status': 'fail'}
    try:
        import Grasshopper
        canvas = Grasshopper.Instances.ActiveCanvas
        server = Grasshopper.Instances.DocumentServer
        doc = canvas.Document if canvas is not None else None
        if doc is None or server.DocumentCount != 1:
            raise RuntimeError('Expected exactly one active test document')
        objects = list(doc.Objects)
        names = set(str(obj.NickName) for obj in objects)
        if len(objects) != 12 or not NAMES.issubset(names) or doc.FilePath:
            raise RuntimeError('Active document is not the unsaved 12-object test')
        before = Rhino.RhinoDoc.ActiveDoc.Objects.Count
        canvas.Document = None
        server.RemoveDocument(doc)
        doc.Dispose()
        after = Rhino.RhinoDoc.ActiveDoc.Objects.Count
        result = {'status': 'pass' if server.DocumentCount == 0 and
                  canvas.Document is None and before == after else 'fail',
                  'grasshopper_documents_after': server.DocumentCount,
                  'rhino_objects_before': before, 'rhino_objects_after': after}
    except Exception:
        result['error'] = traceback.format_exc()
    with open(REPORT, 'w') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True))
    Rhino.RhinoApp.WriteLine('Visible cleanup result: ' + REPORT)
    Rhino.RhinoApp.WriteLine('Visible cleanup status: ' + result['status'])


if __name__ == '__main__':
    main()
