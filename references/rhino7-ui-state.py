"""Read-only Rhino 7 and Grasshopper UI state for native acceptance."""
import json
import os
import traceback

import Rhino


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'rhino7-ui-state.json')


def main():
    result = {'status': 'fail'}
    try:
        import Grasshopper
        canvas = Grasshopper.Instances.ActiveCanvas
        editor = Grasshopper.Instances.DocumentEditor
        server = Grasshopper.Instances.DocumentServer
        active = canvas.Document if canvas is not None else None
        rhino_doc = Rhino.RhinoDoc.ActiveDoc
        result = {
            'status': 'pass',
            'rhino_version': str(Rhino.RhinoApp.Version),
            'rhino_document_name': rhino_doc.Name if rhino_doc else None,
            'rhino_object_count': rhino_doc.Objects.Count if rhino_doc else None,
            'grasshopper_editor_visible': bool(editor is not None and editor.Visible),
            'grasshopper_document_count': server.DocumentCount if server else None,
            'active_grasshopper_document': active.DisplayName if active else None,
        }
    except Exception:
        result['error'] = traceback.format_exc()
    with open(REPORT, 'w') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True))
    Rhino.RhinoApp.WriteLine('UI state result: ' + REPORT)


if __name__ == '__main__':
    main()
