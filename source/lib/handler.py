from AppKit import NSTextAlignmentCenter
from fontTools.misc.fixedTools import otRound
from mojo.subscriber import Subscriber
from mojo.UI import CurrentGlyphWindow, getDefault
from mojo.extensions import getExtensionDefault
from importlib import reload
import ezui
import tools

reload(tools)


class Handler(Subscriber, ezui.WindowController):
    debug = True

    def build(self, parent):
        content = """
        Change Handle Length
        [_ _]       @value

        ---

        (Apply)     @apply
        (Cancel)    @cancel
        """
        descriptionData = dict(
            value=dict(
                valueType="float",
                valueIncrement=1,
                value=0,
            ),
            apply=dict(
                width="fill",
            ),
            cancel=dict(
                width="fill",
                keyEquivalent=chr(27),
            ),
        )
        self.w = ezui.EZPopUp(
            content=content,
            descriptionData=descriptionData,
            controller=self,
            parent=parent,
            size="auto",
            defaultButton="apply",
        )

        # Set up Merz container
        self.glyph_editor = CurrentGlyphWindow()
        self.fg_container = self.glyph_editor.extensionContainer(
            identifier="Handler.foreground", location="foreground", clear=True
        )
        self.bg_container = self.glyph_editor.extensionContainer(
            identifier="Handler.background", location="background", clear=True
        )

        # Set window values
        prefs = getExtensionDefault(tools.EXT_KEY, fallback=self.w.getItemValues())
        self.w.setItemValues(prefs)

        # Allow for arrow keys despite operators being present
        text_field = self.w.getItem("value")
        self.value_operator = ""
        self.number_from_string = text_field._stringToValueConverter
        self.number_to_string = text_field._valueToStringConverter
        text_field._stringToValueConverter = self.operation_from_string
        text_field._valueToStringConverter = self.operation_to_string
        # Set alignment to center
        text_field.getNSTextField().setAlignment_(NSTextAlignmentCenter)
        # Set value
        self.valueCallback(text_field)

    def started(self):
        self.w.open()

    def destroy(self):
        self.clear_all_sublayers()

    # UI OPERATIONS

    def operation_from_string(self, text):
        """Store the operator prefix and convert the remaining text to a number"""
        text = text.strip()
        self.value_operator = ""

        if text.startswith(("*", "/", "=", "+")):
            self.value_operator = text[0]
            text = text[1:].strip()

        return self.number_from_string(text)

    def operation_to_string(self, value):
        """Format the number without duplicating its sign."""
        text = self.number_to_string(value)
        operator = self.value_operator
        if operator == "+" and text.startswith("-"):
            operator = ""
        return operator + text

    # CALLBACKS

    def valueCallback(self, sender):
        text_field = self.w.getItem("value")
        self.value = str(text_field.getNSTextField().stringValue()).strip()
        self.glyph = CurrentGlyph()
        self.draw_preview()

    def cancelCallback(self, sender):
        self.clear_all_sublayers()
        self.w.close()

    def applyCallback(self, sender):
        tools.change_handle_length(self.value, self.glyph)
        self.w.close()

    # MERZ DISPLAY

    def draw_preview(self):
        self.clear_all_sublayers()
        self.w.getItem("apply").enable(False)

        if self.glyph is None or not self.glyph.bounds:
            return

        try:
            tools.calc_operation(1, self.value)
        except (ValueError, ZeroDivisionError):
            return

        self.w.getItem("apply").enable(True)

        # Clear previous drawing
        self.clear_all_sublayers()

        g_copy = self.glyph.copy()
        tools.copy_selection(self.glyph, g_copy)
        tools.change_handle_length(self.value, g_copy)

        # Filter which contours get a stroke
        visible_contours = [
            contour for contour in g_copy.contours if tools.has_selected_points(contour)
        ]

        # Draw the contours’ shape
        self.stroked_preview = self.bg_container.appendPathSublayer(
            strokeColor=(0.8, 0, 0, 1), fillColor=(1, 0, 0, 0), strokeWidth=1
        )
        pen = self.stroked_preview.getPen()
        for contour in visible_contours:
            contour.draw(pen)

        # Draw the points and info
        sel_stroke = getDefault("glyphViewSelectionStrokeWidth")
        radius = getDefault("glyphViewOnCurvePointsSize") + sel_stroke / 2
        small_radius = getDefault("glyphViewOffCurvePointsSize") + sel_stroke / 2
        font_size = getDefault("textFontSize")
        bpts = [bpt for contour in visible_contours for bpt in contour.bPoints]
        sel_pt_coords = [
            (pt.x, pt.y) for pt in g_copy.selectedPoints if pt.type == "offcurve"
        ]
        for bpt in bpts:
            show_on_curve = True
            for coord in [bpt.bcpIn, bpt.bcpOut]:
                adj_coord = (bpt.anchor[0] + coord[0], bpt.anchor[1] + coord[1])
                if adj_coord == bpt.anchor:
                    continue

                if not bpt.selected and adj_coord not in sel_pt_coords:
                    show_on_curve = False
                    continue

                # Handles
                self.fg_container.appendLineSublayer(
                    startPoint=bpt.anchor,
                    endPoint=adj_coord,
                    strokeColor=(1, 0, 0, 1),
                    strokeWidth=sel_stroke,
                )

                # Handle points
                self.fg_container.appendSymbolSublayer(
                    imageSettings=dict(
                        name="oval",
                        size=(small_radius * 2, small_radius * 2),
                        fillColor=(1, 0, 0, 1),
                        strokeColor=None,
                    ),
                    position=adj_coord,
                )

                # Handle info
                distance = tools.calc_dist((0, 0), coord)
                text_line_layer = self.fg_container.appendTextLineSublayer(
                    position=adj_coord,
                    size=(800, 50),
                    backgroundColor=None,
                    text=f"L={otRound(distance)}",
                    fillColor=(1, 0, 0, 1),
                    horizontalAlignment="center",
                    offset=(0, -8),
                )
                text_line_layer.setPointSize(font_size)

            if show_on_curve:
                # On-curves
                self.fg_container.appendSymbolSublayer(
                    imageSettings=dict(
                        name="oval",
                        size=(radius * 2, radius * 2),
                        fillColor=(1, 0, 0, 1),
                        strokeColor=None,
                    ),
                    position=bpt.anchor,
                )

    def clear_all_sublayers(self):
        self.fg_container.clearSublayers()
        self.bg_container.clearSublayers()

    # SUBSCRIBERS

    def glyphEditorDidMouseUp(self, info):
        self.glyph = info["glyph"]
        if self.glyph.bounds:
            self.draw_preview()

    def glyphEditorDidSetGlyph(self, info):
        self.glyph = info["glyph"]
        if self.glyph.bounds:
            self.draw_preview()


if tools.glyph_has_selected_points(CurrentGlyph()):
    Handler(parent=CurrentGlyphWindow().editGlyphView)
