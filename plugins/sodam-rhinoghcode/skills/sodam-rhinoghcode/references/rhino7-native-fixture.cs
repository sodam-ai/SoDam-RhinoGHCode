using System;
using System.Collections.Generic;
using Rhino.Geometry;

// Compile-check wrapper. In Rhino 7's legacy C# Script editor, configure four
// outputs (PolyPts, BoundsPts, B, Status) and paste only the RunScript body.
public class Script_Instance
{
  private void RunScript(ref object PolyPts, ref object BoundsPts, ref object B, ref object Status)
  {
    PolyPts = new List<Point3d>
    {
      new Point3d(0, 0, 0),
      new Point3d(2, 0, 0),
      new Point3d(2, 4, 0)
    };
    BoundsPts = new List<Point3d>
    {
      new Point3d(4, -2, 6),
      new Point3d(-1, 8, 3),
      new Point3d(2, 0, -5)
    };
    B = null;
    Status = "FAIL: no planar face with an inner trim";

    Curve outer = new Rectangle3d(
      Plane.WorldXY, new Interval(0, 10), new Interval(0, 10)).ToNurbsCurve();
    Curve inner = new Circle(Plane.WorldXY, new Point3d(5, 5, 0), 2).ToNurbsCurve();
    Brep[] candidates = Brep.CreatePlanarBreps(new Curve[] { outer, inner }, 0.01);
    if (candidates == null) return;
    foreach (Brep candidate in candidates)
    {
      if (candidate == null || !candidate.IsValid || candidate.Faces.Count != 1) continue;
      if (candidate.Faces[0].Loops.Count < 2) continue;
      B = candidate;
      Status = "PASS: planar face with an inner trim";
      return;
    }
  }
}
