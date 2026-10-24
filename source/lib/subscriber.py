from fontTools.misc.fixedTools import otRound
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber
from mojo.UI import getDefault, appearanceColorKey
from importlib import reload
import tools

reload(tools)


class HandlerInfo(Subscriber):
    debug = True

    def build(
        self,
    ):
        self.glyph = None
        self.glyph_editor = self.getGlyphEditor()
        self.container = self.glyph_editor.extensionContainer(
            identifier="Handler.foreground", location="foreground", clear=True
        )

    def destroy(self):
        self.container.clearSublayers()

    def draw_info(self):
        self.container.clearSublayers()

        if not (self.glyph or self.glyph.bounds or self.glyph.selectedPoints):
            return

        # Draw the points and info
        text_color = getDefault(appearanceColorKey("glyphViewPointLabelColor"))
        font_size = getDefault("textFontSize")
        # Handle when on-curves are selected
        coords_and_dists = set()
        for bpt in self.glyph.selectedBPoints:
            for coord in [bpt.bcpIn, bpt.bcpOut]:
                adj_coord = (bpt.anchor[0] + coord[0], bpt.anchor[1] + coord[1])
                if adj_coord == bpt.anchor:
                    continue
                distance = tools.calc_dist((0, 0), coord)
                coords_and_dists.add((adj_coord, distance))

        # Handle when off-curves are explicity selected
        for pt in self.glyph.selectedPoints:
            if pt.type != "offcurve":
                continue
            points = pt.contour.points
            i = pt.index
            prev_pt = points[i - 1]
            next_pt = points[i - len(points) + 1]
            # Capture the base point and the opposite point
            if prev_pt.type != "offcurve":
                base_pt = prev_pt
                opposite_pt = points[i - 2]
            elif next_pt.type != "offcurve":
                base_pt = next_pt
                opposite_pt = points[i - len(points) + 2]
            else:
                continue
            # Show distance from base on-curve
            base = (base_pt.x, base_pt.y)
            handle = (pt.x, pt.y)
            distance = tools.calc_dist(base, handle)
            coords_and_dists.add((handle, distance))
            # Show distance of opposite handle from base on-curve
            opposite_handle = (opposite_pt.x, opposite_pt.y)
            distance = tools.calc_dist(base, opposite_handle)
            coords_and_dists.add((opposite_handle, distance))

        # Draw info
        for coord, distance in coords_and_dists:
            text_line_layer = self.container.appendTextLineSublayer(
                position=coord,
                size=(0, 0),
                backgroundColor=None,
                text=f"L={otRound(distance)}",
                fillColor=text_color,
                horizontalAlignment="center",
                offset=(0, -8),
            )
            text_line_layer.setPointSize(font_size)
            text_line_layer.setWeight("semibold")

    def glyphEditorGlyphDidEndChangeSelection(self, info):
        self.glyph = info["glyph"]
        self.draw_info()

    def glyphEditorDidSetGlyph(self, info):
        self.glyph = info["glyph"]
        self.draw_info()

    def glyphEditorDidMouseDrag(self, info):
        self.glyph = info["glyph"]
        self.draw_info()

    def glyphEditorDidUndo(self, info):
        self.glyph = info["glyph"]
        self.draw_info()


# registerGlyphEditorSubscriber(HandlerInfo)
