"""Validate the stored canonical orbit reps reproduce optimal solutions."""
import json

from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import penalties_for_px


def main(path="output/orbit_reps_report.json"):
    grid = HexGrid()
    with open(path, encoding='utf-8') as f:
        recs = json.load(f)
    print("orb | sides OK | wedges(s) | rays(s) | pen")
    for r in recs:
        p = tuple(r['canon_p'])
        x = tuple(r['canon_x'])
        side, wedge, ray, pen = penalties_for_px(grid, p, x)
        sides_ok = all(v == 1355 for v in side)
        print(f"{r['orbit']:3d} | {str(sides_ok):>9} | {sorted(wedge)} | {sorted(ray)} | {pen}")


if __name__ == "__main__":
    main()
