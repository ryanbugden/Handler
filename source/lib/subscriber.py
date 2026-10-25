from fontTools.misc.fixedTools import otRound
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber
from mojo.UI import getDefault, appearanceColorKey
from importlib import reload
import tools

reload(tools)


class HandlerInfo(Subscriber):
    debug = True

    def build(self):
        self.glyph = None
        self.glyph_editor = self.getGlyphEditor()
        self.container = self.glyph_editor.extensionContainer(
            identifier="info.Handler.foreground", location="foreground", clear=True
        )

    def destroy(self):
        self.container.clearSublayers()

    def draw_info(self):
        self.container.clearSublayers()

        if self.glyph is None or not self.glyph.bounds:
            return

        # Draw the points and info
        text_color = getDefault(appearanceColorKey("glyphViewPointLabelColor"))
        font_size = getDefault("textFontSize")

        # Collect data: coordinates to draw on, and distance data to write
        for pt, data in tools.selected_handles(self.glyph.contours).items():
            base_pt = data["base"]
            base = (base_pt.x, base_pt.y)
            handle = (pt.x, pt.y)
            # Skip same coordinate
            if handle == base:
                continue
            distance = tools.calc_dist(base, handle)
            text_line_layer = self.container.appendTextLineSublayer(
                position=handle,
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
