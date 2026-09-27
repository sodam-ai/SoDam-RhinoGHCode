"""Export the isolated Grasshopper test canvas with Rhino 7's own renderer."""
import clr
import json
import math
import os
import traceback

import Rhino


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'rhino7-canvas-export-result.json')
IMAGE = os.path.join(ROOT, 'references', 'rhino7-canvas-native.png')


def main():
    result = {'status': 'fail'}
    try:
        import Grasshopper
        from Grasshopper.GUI.Canvas import GH_Canvas
        from System.Drawing import Rectangle, Size
        canvas = Grasshopper.Instances.ActiveCanvas
        doc = canvas.Document if canvas is not None else None
        if doc is None or len(list(doc.Objects)) != 12:
            raise RuntimeError('Expected the isolated 12-object GH test canvas')
        bounds = [obj.Attributes.Bounds for obj in doc.Objects]
        left = int(math.floor(min(rect.Left for rect in bounds))) - 30
        top = int(math.floor(min(rect.Top for rect in bounds))) - 30
        right = int(math.ceil(max(rect.Right for rect in bounds))) + 30
        bottom = int(math.ceil(max(rect.Bottom for rect in bounds))) + 30
        area = Rectangle(left, top, right - left, bottom - top)
        settings = GH_Canvas.GH_ImageSettings(IMAGE)
        settings.Zoom = 1.0
        rendered_size = clr.Reference[Size]()
        generated = canvas.GenerateHiResImage(area, settings, rendered_size)
        paths = [str(path) for path in generated]
        result = {'status': 'pass' if paths and all(os.path.isfile(p) for p in paths)
                  else 'fail', 'paths': paths,
                  'bounds': [left, top, right, bottom],
                  'rhino_object_count': Rhino.RhinoDoc.ActiveDoc.Objects.Count}
    except Exception:
        result['error'] = traceback.format_exc()
    with open(REPORT, 'w') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True))
    Rhino.RhinoApp.WriteLine('Canvas export result: ' + REPORT)
    Rhino.RhinoApp.WriteLine('Canvas export status: ' + result['status'])


if __name__ == '__main__':
    main()
