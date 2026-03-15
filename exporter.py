"""Bitmap→vector tracing and TTF font generation."""

import numpy as np
from PIL import Image
from skimage.measure import find_contours, approximate_polygon
from fontTools.fontBuilder import FontBuilder


CANVAS_SIZE = 512
UPM = 1000  # Units per em
SCALE = UPM / CANVAS_SIZE


def signed_area(points):
    """Compute signed area. Positive = counter-clockwise in math coords."""
    n = len(points)
    if n < 3:
        return 0
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return area / 2.0


def trace_glyph(pil_image, tolerance=2.0):
    """Convert a PIL grayscale image to a list of contours in font coordinates.

    Returns list of contours, where each contour is a list of (x, y) tuples
    in font coordinate space (y-up, 0-1000 range).
    """
    arr = np.array(pil_image)
    binary = (arr > 128).astype(np.float64)

    raw_contours = find_contours(binary, level=0.5)
    if not raw_contours:
        return []

    contours = []
    for raw in raw_contours:
        # Simplify contour
        simplified = approximate_polygon(raw, tolerance=tolerance)
        if len(simplified) < 3:
            continue

        # Convert from (row, col) = (y_down, x) to font coords (x, y_up)
        font_points = []
        for row, col in simplified:
            x = col * SCALE
            y = (CANVAS_SIZE - row) * SCALE
            font_points.append((round(x), round(y)))

        # Remove duplicate closing point if present
        if font_points[0] == font_points[-1]:
            font_points = font_points[:-1]

        if len(font_points) < 3:
            continue

        contours.append(font_points)

    # Sort contours: largest bounding area first (outer contours)
    def bbox_area(pts):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    contours.sort(key=bbox_area, reverse=True)

    # Fix winding direction: TrueType wants outer=clockwise (negative signed area in math)
    # and inner=counter-clockwise (positive signed area in math)
    if contours:
        for i, pts in enumerate(contours):
            sa = signed_area(pts)
            if i == 0:
                # Outer contour: should be clockwise (negative area)
                if sa > 0:
                    contours[i] = list(reversed(pts))
            else:
                # Inner contour: should be counter-clockwise (positive area)
                if sa < 0:
                    contours[i] = list(reversed(pts))

    return contours


def build_font(glyph_data, font_name="MyFont", style="Regular", output_path="output.ttf",
               tolerance=2.0, progress_callback=None, is_ttf=True):
    """Build a TTF or OTF font from glyph images.

    Args:
        glyph_data: dict of {char: PIL.Image} or {char: filepath}
        font_name: font family name
        style: font style name
        output_path: where to save the font file
        tolerance: contour simplification tolerance
        progress_callback: callable(current, total) for progress updates
        is_ttf: True for TTF (TrueType outlines), False for OTF (CFF outlines)
    """
    # Collect glyphs and trace contours
    glyph_contours = {'.notdef': []}
    char_map = {}
    metrics = {}
    total = len(glyph_data)

    for i, (char, img_or_path) in enumerate(glyph_data.items()):
        if progress_callback:
            progress_callback(i + 1, total)

        glyph_name = f"uni{ord(char):04X}"
        char_map[ord(char)] = glyph_name

        # Space character: no contours, fixed advance width
        if char == ' ':
            glyph_contours[glyph_name] = []
            metrics[glyph_name] = (250, 0)
            continue

        if isinstance(img_or_path, str):
            img = Image.open(img_or_path).convert('L')
        else:
            img = img_or_path

        contours = trace_glyph(img, tolerance=tolerance)
        shifted, adv_w, lsb = _compute_metrics(contours)
        glyph_contours[glyph_name] = shifted
        metrics[glyph_name] = (adv_w, lsb)

    metrics['.notdef'] = (500, 0)

    # Build font
    fb = FontBuilder(UPM, isTTF=is_ttf)
    fb.setupGlyphOrder(list(glyph_contours.keys()))

    if is_ttf:
        fb.setupGlyf({
            name: _draw_ttf_glyph(contours)
            for name, contours in glyph_contours.items()
        })
    else:
        _setup_cff(fb, glyph_contours, metrics, font_name)

    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupCharacterMap(char_map)
    ps_name = font_name.replace(" ", "") + "-" + style.replace(" ", "")
    fb.setupNameTable({
        "familyName": font_name,
        "styleName": style,
        "uniqueFontIdentifier": f"{font_name} {style}",
        "fullName": f"{font_name} {style}",
        "version": "Version 1.0",
        "psName": ps_name,
    })
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, sTypoLineGap=0)
    fb.setupPost()

    fb.font.save(output_path)
    return output_path


def _compute_metrics(contours, padding=30):
    """Compute per-glyph metrics and shift contours to start near x=0.

    Returns (shifted_contours, advance_width, lsb).
    """
    if not contours:
        return contours, 500, 0

    # Find bounding box across all contour points
    all_x = [x for contour in contours for x, y in contour]
    if not all_x:
        return contours, 500, 0

    x_min = min(all_x)
    x_max = max(all_x)

    # Shift so glyph starts at x=padding
    shift = x_min - padding
    if shift < 0:
        shift = 0

    shifted = []
    for contour in contours:
        shifted.append([(x - shift, y) for x, y in contour])

    advance_width = (x_max - x_min) + 2 * padding
    lsb = max(x_min - shift, 0)

    return shifted, round(advance_width), round(lsb)


def _draw_ttf_glyph(contours):
    """Convert contour points to a TrueType glyph."""
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen(None)

    if not contours:
        pen.moveTo((0, 0))
        pen.lineTo((0, 0))
        pen.endPath()
        return pen.glyph()

    for contour in contours:
        if len(contour) < 3:
            continue
        pen.moveTo(contour[0])
        for pt in contour[1:]:
            pen.lineTo(pt)
        pen.closePath()

    return pen.glyph()


def _setup_cff(fb, glyph_contours, metrics, font_name):
    """Set up CFF (OTF) outlines using T2CharStringPen."""
    from fontTools.pens.t2CharStringPen import T2CharStringPen

    charstrings = {}
    for name, contours in glyph_contours.items():
        adv_w = metrics.get(name, (500, 0))[0]
        pen = T2CharStringPen(adv_w, None)
        if contours:
            for contour in contours:
                if len(contour) < 3:
                    continue
                pen.moveTo(contour[0])
                for pt in contour[1:]:
                    pen.lineTo(pt)
                pen.closePath()
        charstrings[name] = pen.getCharString()

    fb.setupCFF(
        psName=font_name,
        fontInfo={},
        charStringsDict=charstrings,
        privateDict={},
    )
