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


def set_dist_bpt(bpt, distance, direction="in"):
    """Set the distance of a b-point’s handle"""
    attr = f"bcp{direction.title()}"
    handle = getattr(bpt, attr)
    # Skip no-handles
    if handle == (0, 0):
        return
    angle = calc_angle((0, 0), handle)
    # Calculate new position, using angle
    new_pos = (
        my_round(distance * math.cos(angle)),
        my_round(distance * math.sin(angle)),
    )
    setattr(bpt, attr, new_pos)


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
        # Handle when on-curves are selected (in RoboFont, the off-curves are highlighted, which suggests selection)
        for bpt in glyph.selectedBPoints:
            for direction in ("in", "out"):
                attr = f"bcp{direction.title()}"
                handle = getattr(bpt, attr)
                distance = calc_dist((0, 0), handle)
                new_dist = calc_operation(distance, input_text)
                set_dist_bpt(bpt, new_dist, direction=direction)
        # Handle when off-curves are explicity selected
        for pt in glyph.selectedPoints:
            if pt.type != "offcurve":
                continue
            points = pt.contour.points
            i = pt.index
            prev_pt = points[i - 1]
            next_pt = points[i - len(points) + 1]
            if prev_pt.type != "offcurve":
                base_pt = prev_pt
            elif next_pt.type != "offcurve":
                base_pt = next_pt
            else:
                continue
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
