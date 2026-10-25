import math
from mojo.UI import getDefault


EXT_KEY = "com.ryanbugden.handler"


def my_round(value):
    round_value = getDefault("glyphViewRoundValues")
    if round_value == 0:
        return value
    return round_value * round(value / round_value)


def calc_angle(p1, p2):
    dx, dy = calc_vector(p1, p2)
    return math.atan2(dy, dx)


def calc_vector(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return x2 - x1, y2 - y1


def calc_dist(p1, p2):
    return math.hypot(*calc_vector(p1, p2))


def calc_operation(distance, text):
    """
    Parse text that asserts addition, subtraction,
    multiplication, division, and absolute length.
    """
    if "=" in text:
        return float(text.split("=")[-1].strip())
    elif "/" in text:
        return distance / float(text.split("/")[-1].strip())
    elif "*" in text:
        return distance * float(text.split("*")[-1].strip())
    elif "+" in text:
        return distance + float(text.split("+")[-1].strip())
    else:
        return distance + float(text.strip())


def set_dist_pt(pt, base_coord, distance):
    """Set a handle point’s distance from its base on-curve."""
    handle = (pt.x, pt.y)
    # Skip handles with same coord as base on-curve
    if handle == base_coord:
        return
    # Calculate new position, using angle
    angle = calc_angle(base_coord, handle)
    base_x, base_y = base_coord
    pt.x = my_round(base_x + distance * math.cos(angle))
    pt.y = my_round(base_y + distance * math.sin(angle))


def change_handle_length(input_text, glyph):
    with glyph.undo("Change handle length"):
        for pt, data in selected_handles(glyph.contours).items():
            base_pt = data["base"]
            base = (base_pt.x, base_pt.y)
            handle = (pt.x, pt.y)
            distance = calc_dist(base, handle)
            new_dist = calc_operation(distance, input_text)
            set_dist_pt(pt, base, new_dist)
    glyph.changed()


def copy_selection(source, target):
    """Copy point and b-point selection states from source to target"""
    for source_contour, target_contour in zip(source.contours, target.contours):
        for source_pt, target_pt in zip(source_contour.points, target_contour.points):
            target_pt.selected = source_pt.selected
        for source_bpt, target_bpt in zip(
            source_contour.bPoints, target_contour.bPoints
        ):
            target_bpt.selected = source_bpt.selected


def contour_has_selected_points(contour):
    for pt in contour.points:
        if pt.selected:
            return True
    for bpt in contour.bPoints:
        if bpt.selected:
            return True
    return False


def glyph_has_selected_points(glyph):
    for contour in glyph.contours:
        if contour_has_selected_points(contour):
            return True
    return False


def selected_handles(contours):
    """Map selected handles and handles of selected on-curves to base/opposite points."""
    handles = {}
    for contour in contours:
        points = contour.points
        for i, pt in enumerate(points):
            # Only interested in off-curves
            if pt.type != "offcurve":
                continue
            # Capture the base point and the opposite point
            prev_pt = points[i - 1]
            next_pt = points[i - len(points) + 1]
            opposite_pt = None
            if prev_pt.type != "offcurve":
                base = prev_pt
                if not contour.open or i >= 2:
                    opposite_pt = points[i - 2]
            elif next_pt.type != "offcurve":
                base = next_pt
                if not contour.open or i + 2 < len(points):
                    opposite_pt = points[i - len(points) + 2]
            else:
                continue
            # Check whether selected
            if not (pt.selected or base.selected):
                continue
            # Get opposite point if it's a handle
            opposite = None
            if opposite_pt is not None and opposite_pt.type == "offcurve":
                opposite = opposite_pt
            handles[pt] = dict(base=base, opposite=opposite)

    return handles
