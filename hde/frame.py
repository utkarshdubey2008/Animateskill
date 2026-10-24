"""Compose one frame from the map plate, markers, arrows, and captions."""

from __future__ import annotations

import functools
import math
import random
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from hde.fonts import FontPaths
from hde.geom import camera_window, crop_box, lerp, project, pulse, smoothstep
from hde.model import Documentary, MarkerDef, MarkerKey, Scene

PAPER = (243, 239, 228)
MUTED = (196, 188, 170)
GOLD = (226, 177, 90)
INK = (12, 14, 12)


@dataclass
class FrameContext:
    doc: Documentary
    base: Image.Image
    width: int
    height: int
    fps: int
    fonts: FontPaths
    scrim: Image.Image
    black: Image.Image
    storm: Image.Image
    badge: str | None


def make_scrim(width: int, height: int) -> Image.Image:
    """Top fade for the title, and a solid lower band so captions stay readable."""
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    top = max(24, int(height * 0.16))
    for y in range(top):
        alpha = int(210 * (1.0 - y / top) ** 1.05)
        draw.line([(0, y), (width, y)], fill=(8, 10, 12, alpha))
    fade = max(18, int(height * 0.07))
    solid = max(56, int(height * 0.18))
    band = fade + solid
    for step in range(band):
        y = height - band + step
        if step < fade:
            alpha = int(245 * (step / fade))
        else:
            alpha = 245
        draw.line([(0, y), (width, y)], fill=(6, 8, 10, alpha))
    return image


def compose_scene(ctx: FrameContext, scene: Scene, t: float, frame_index: int) -> Image.Image:
    eased = smoothstep(t)
    camera_x = lerp(scene.camera_start.cx, scene.camera_end.cx, eased)
    camera_y = lerp(scene.camera_start.cy, scene.camera_end.cy, eased)
    zoom = lerp(scene.camera_start.zoom, scene.camera_end.zoom, eased)
    map_w, map_h = ctx.base.size
    window = camera_window(camera_x, camera_y, zoom, map_w, map_h, ctx.width / ctx.height)
    box = crop_box(window, map_w, map_h)
    crop = ctx.base.crop(box)
    frame = crop.resize((ctx.width, ctx.height), Image.Resampling.BILINEAR)

    rain_amount = 0.0
    for effect in scene.effects:
        if effect.type == "rain":
            rain_amount = max(rain_amount, pulse(t, effect.t0, effect.t1, 0.06) * effect.intensity)
    if rain_amount > 0.01:
        frame = Image.blend(frame, ctx.storm, 0.32 * rain_amount)

    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if rain_amount > 0.01:
        _draw_rain(draw, ctx.width, ctx.height, frame_index, rain_amount)
    for arrow in scene.arrows:
        _draw_arrow(draw, ctx, scene, arrow, t, box, map_w, map_h)
    for effect in scene.effects:
        if effect.type == "artillery":
            _draw_artillery(draw, ctx, effect, t, frame_index, box, map_w, map_h)
    for marker_id in scene.show:
        _draw_marker(draw, ctx, scene, ctx.doc.markers[marker_id], t, box, map_w, map_h)
    frame.paste(overlay, (0, 0), overlay)
    del overlay

    frame.paste(ctx.scrim, (0, 0), ctx.scrim)
    _draw_cards(frame, ctx, scene, t)
    _draw_ui(frame, ctx, scene)
    return frame


def _draw_rain(draw: ImageDraw.ImageDraw, width: int, height: int, frame_index: int, amount: float) -> None:
    generator = random.Random(frame_index * 997)
    scale = height / 720
    count = int(100 * amount * scale)
    length = max(8, int(20 * scale))
    wind = max(3, int(8 * scale))
    color = (186, 206, 214, int(150 * min(1.0, amount)))
    for _ in range(count):
        x = generator.randrange(0, width)
        y = generator.randrange(0, height)
        draw.line([(x, y), (x - wind, y + length)], fill=color, width=1)


def _draw_arrow(draw, ctx: FrameContext, scene: Scene, arrow, t: float, box, map_w: int, map_h: int) -> None:
    if t <= arrow.t0:
        return
    progress = 1.0 if t >= arrow.t1 else (t - arrow.t0) / (arrow.t1 - arrow.t0)
    x1 = lerp(arrow.x0, arrow.x1, progress)
    y1 = lerp(arrow.y0, arrow.y1, progress)
    x0, y0 = project(arrow.x0, arrow.y0, box, ctx.width, ctx.height, map_w, map_h)
    tip_x, tip_y = project(x1, y1, box, ctx.width, ctx.height, map_w, map_h)
    scale = ctx.height / 720
    color = (232, 220, 190, 230)
    width = max(2, int(round(3 * scale)))
    if arrow.confidence == "illustrative":
        _dashed_line(draw, x0, y0, tip_x, tip_y, color, width, max(8, int(14 * scale)), max(5, int(8 * scale)))
    else:
        draw.line([(x0, y0), (tip_x, tip_y)], fill=color, width=width)
    _arrow_head(draw, x0, y0, tip_x, tip_y, color, max(10, int(14 * scale)))
    if progress < 0.45:
        return
    mid_x = lerp(x0, tip_x, 0.42)
    mid_y = lerp(y0, tip_y, 0.42)
    dx, dy = tip_x - x0, tip_y - y0
    dist = math.hypot(dx, dy) or 1.0
    off = max(10, int(16 * scale))
    label_x = mid_x + (-dy / dist) * off
    label_y = mid_y + (dx / dist) * off
    font = _font(ctx.fonts.sans_bold, _px(14, ctx.height))
    _label_box(draw, label_x, label_y, [arrow.label], font, None, PAPER, "center", int(255 * 0.95))


def _draw_artillery(draw, ctx, effect, t, frame_index, box, map_w, map_h) -> None:
    amount = pulse(t, effect.t0, effect.t1, 0.04)
    if amount <= 0 or frame_index % 8 > 2:
        return
    marker = ctx.doc.markers[effect.marker]
    sx, sy = project(marker.x, marker.y, box, ctx.width, ctx.height, map_w, map_h)
    scale = ctx.height / 720
    phase = frame_index % 8
    radius = max(4, int((8 + phase * 3) * scale))
    jitter = ((frame_index * 17) % 11) - 5
    color = ctx.doc.palette[marker.side]
    alpha = int(170 * amount)
    draw.ellipse(
        [sx - radius + jitter, sy - radius, sx + radius + jitter, sy + radius],
        fill=(*color, alpha),
    )
    inner = max(2, radius // 2)
    draw.ellipse(
        [sx - inner, sy - inner, sx + inner, sy + inner],
        fill=(255, 244, 220, int(210 * amount)),
    )


def _draw_marker(draw, ctx, scene: Scene, marker: MarkerDef, t: float, box, map_w, map_h) -> None:
    state = _marker_state(marker, scene.overrides.get(marker.id, []), t)
    if state["alpha"] <= 0.02:
        return
    sx, sy = project(marker.x, marker.y, box, ctx.width, ctx.height, map_w, map_h)
    if sx < -80 or sy < -80 or sx > ctx.width + 80 or sy > ctx.height + 80:
        return
    scale = ctx.height / 720
    radius = max(4, int(round(9 * scale)))
    alpha = int(255 * state["alpha"])
    color = ctx.doc.palette[marker.side]
    if marker.confidence == "attested_area":
        draw.ellipse(
            [sx - radius, sy - radius, sx + radius, sy + radius],
            fill=(*color, alpha),
            outline=(20, 16, 12, alpha),
            width=max(1, int(2 * scale)),
        )
    else:
        draw.ellipse(
            [sx - radius, sy - radius, sx + radius, sy + radius],
            outline=(*color, alpha),
            width=max(2, int(3 * scale)),
        )
    if state["mark"] == "killed":
        span = radius + max(3, int(4 * scale))
        kill = (*PAPER, alpha)
        width = max(2, int(2 * scale))
        draw.line([(sx - span, sy - span), (sx + span, sy + span)], fill=kill, width=width)
        draw.line([(sx - span, sy + span), (sx + span, sy - span)], fill=kill, width=width)
    title_font = _font(ctx.fonts.sans_bold, _px(15, ctx.height))
    detail_font = _font(ctx.fonts.sans, _px(13, ctx.height))
    _place_marker_label(
        draw,
        ctx,
        sx,
        sy,
        radius,
        marker.anchor,
        state["label"],
        state["detail"],
        title_font,
        detail_font,
        alpha,
    )


def _marker_state(marker: MarkerDef, keys: list[MarkerKey], t: float) -> dict:
    detail = marker.detail
    mark = ""
    for key in keys:
        if key.t > t:
            break
        if key.detail is not None:
            detail = key.detail
        if key.mark is not None:
            mark = key.mark
    return {
        "label": marker.label,
        "detail": detail,
        "mark": mark,
        "alpha": _alpha_at(keys, t),
    }


def _alpha_at(keys: list[MarkerKey], t: float) -> float:
    keyed = [key for key in keys if key.alpha is not None]
    if not keyed:
        return 1.0
    if t <= keyed[0].t:
        return float(keyed[0].alpha)
    for earlier, later in zip(keyed, keyed[1:]):
        if t <= later.t:
            span = later.t - earlier.t or 1.0
            return lerp(float(earlier.alpha), float(later.alpha), (t - earlier.t) / span)
    return float(keyed[-1].alpha)


def _place_marker_label(draw, ctx, sx, sy, radius, anchor, title, detail, title_font, detail_font, alpha) -> None:
    pad = max(3, int(4 * ctx.height / 720))
    title_w = draw.textlength(title, font=title_font)
    detail_w = draw.textlength(detail, font=detail_font)
    title_h = _text_height(title_font)
    detail_h = _text_height(detail_font)
    box_w = int(max(title_w, detail_w) + pad * 2)
    box_h = int(title_h + detail_h + pad * 2 + 1)
    gap = radius + max(8, int(14 * ctx.height / 720))
    if anchor == "e":
        origin_x, origin_y = sx + gap, sy - box_h / 2
    elif anchor == "w":
        origin_x, origin_y = sx - gap - box_w, sy - box_h / 2
    elif anchor == "n":
        origin_x, origin_y = sx - box_w / 2, sy - gap - box_h
    else:
        origin_x, origin_y = sx - box_w / 2, sy + gap
    margin = 8
    # Keep labels out of the caption band, but never let one float away from its dot.
    caption_top = ctx.height - int(ctx.height * 0.20)
    origin_x = max(margin, min(origin_x, ctx.width - box_w - margin))
    if origin_y + box_h > caption_top:
        origin_y = caption_top - box_h
    if origin_y < margin:
        origin_y = margin
    if abs((origin_y + box_h / 2) - sy) > box_h + gap + 10:
        return
    fill = (*INK, int(214 * alpha / 255))
    draw.rounded_rectangle(
        [origin_x, origin_y, origin_x + box_w, origin_y + box_h],
        radius=4,
        fill=fill,
    )
    draw.text((origin_x + pad, origin_y + pad), title, font=title_font, fill=(*PAPER, alpha))
    draw.text(
        (origin_x + pad, origin_y + pad + title_h),
        detail,
        font=detail_font,
        fill=(*MUTED, alpha),
    )


def _draw_cards(frame: Image.Image, ctx: FrameContext, scene: Scene, t: float) -> None:
    for card in scene.cards:
        amount = _card_amount(t, card.t0, card.t1)
        if amount <= 0.01:
            continue
        _draw_card(frame, ctx, card.lines, card.accent, amount)


def _card_amount(t: float, t0: float, t1: float) -> float:
    if t < t0 or t > t1:
        return 0.0
    fade = 0.1
    amount = 1.0
    if t < t0 + fade:
        amount = (t - t0) / fade
    if t1 < 0.999 and t > t1 - fade:
        amount = min(amount, (t1 - t) / max(fade, 1e-6))
    return max(0.0, min(1.0, amount))


def _draw_card(frame: Image.Image, ctx: FrameContext, lines: list[str], accent: int, amount: float) -> None:
    scale = ctx.height / 720
    pad_x = max(16, int(36 * scale))
    pad_y = max(12, int(24 * scale))
    max_width = int(ctx.width * 0.72)
    probe = ImageDraw.Draw(frame)
    body_size = _px(26, ctx.height)
    fonts = []
    text_width = 0
    text_height = 0
    gap = max(6, int(10 * scale))
    for line in lines:
        font = _fit_font(probe, ctx.fonts.serif_bold, line, body_size, max_width - pad_x * 2, _px(16, ctx.height))
        fonts.append(font)
        text_width = max(text_width, int(probe.textlength(line, font=font)))
        text_height += _text_height(font)
    text_height += gap * (len(lines) - 1)
    panel_w = text_width + pad_x * 2
    panel_h = text_height + pad_y * 2
    origin_x = (ctx.width - panel_w) // 2
    origin_y = int(ctx.height * 0.36) - panel_h // 2
    panel = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    panel_alpha = int(248 * amount)
    pdraw.rounded_rectangle([0, 0, panel_w - 1, panel_h - 1], radius=8, fill=(10, 12, 14, panel_alpha))
    pdraw.rectangle([pad_x, pad_y - 8, pad_x + min(72, text_width), pad_y - 5], fill=(*GOLD, panel_alpha))
    cursor_y = pad_y
    for index, (line, font) in enumerate(zip(lines, fonts)):
        color = GOLD if index == accent else PAPER
        pdraw.text((pad_x, cursor_y), line, font=font, fill=(*color, int(255 * amount)))
        cursor_y += _text_height(font) + gap
    frame.paste(panel, (origin_x, origin_y), panel)


def _draw_ui(frame: Image.Image, ctx: FrameContext, scene: Scene) -> None:
    draw = ImageDraw.Draw(frame)
    pad = max(12, int(28 * ctx.height / 720))
    title_font = _font(ctx.fonts.sans_bold, _px(26, ctx.height))
    meta_font = _font(ctx.fonts.sans, _px(16, ctx.height))
    date_font = _font(ctx.fonts.sans, _px(18, ctx.height))
    badge_font = _font(ctx.fonts.sans_bold, _px(13, ctx.height))
    title = ctx.doc.title.upper()
    date = ctx.doc.date_label.upper()
    draw.text((pad, pad), title, font=title_font, fill=PAPER)
    date_w = draw.textlength(date, font=date_font)
    draw.text((ctx.width - pad - date_w, pad + 4), date, font=date_font, fill=GOLD)
    line2 = f"{scene.title}   ·   {ctx.doc.location_label}"
    badge = ctx.badge or ""
    badge_w = draw.textlength(badge, font=badge_font) if badge else 0
    available = ctx.width - pad * 2 - badge_w - 20
    if draw.textlength(line2, font=meta_font) > available:
        line2 = scene.title
    line2_y = pad + _text_height(title_font) + 4
    draw.text((pad, line2_y), line2, font=meta_font, fill=MUTED)
    if badge:
        draw.text((ctx.width - pad - badge_w, line2_y + 2), badge, font=badge_font, fill=GOLD)
    _draw_legend(frame, ctx, pad, line2_y + _text_height(meta_font) + 12)
    _draw_caption(ImageDraw.Draw(frame), ctx, scene.narration, pad)


def _draw_legend(frame: Image.Image, ctx: FrameContext, x: int, y: int) -> None:
    probe = ImageDraw.Draw(frame)
    font = _font(ctx.fonts.sans, _px(14, ctx.height))
    line_h = _text_height(font) + 4
    widest = 0
    for item in ctx.doc.legend:
        widest = max(widest, int(probe.textlength(item.text, font=font)))
    swatch_w = max(18, int(28 * ctx.height / 720))
    pad = 8
    box_w = swatch_w + widest + pad * 3
    box_h = line_h * len(ctx.doc.legend) + pad * 2
    panel = Image.new("RGBA", (box_w, box_h), (8, 10, 12, 170))
    pdraw = ImageDraw.Draw(panel)
    for index, item in enumerate(ctx.doc.legend):
        row_y = pad + index * line_h
        _swatch(pdraw, pad, row_y + 2, swatch_w - 8, max(8, int(12 * ctx.height / 720)), item.swatch)
        pdraw.text((pad + swatch_w, row_y), item.text, font=font, fill=PAPER)
    frame.paste(panel, (x, y), panel)


def _swatch(draw, x: int, y: int, width: int, size: int, kind: str) -> None:
    radius = max(4, size // 2)
    cx, cy = x + radius, y + radius
    if kind == "solid":
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(226, 177, 90, 255),
        )
    elif kind == "hollow":
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(224, 196, 170, 255),
            width=2,
        )
    else:
        mid = y + radius
        _dashed_line(draw, x, mid, x + width, mid, (232, 220, 190, 255), 2, 6, 4)


def _draw_caption(draw, ctx: FrameContext, text: str, pad: int) -> None:
    max_width = ctx.width - pad * 2
    start = _px(22, ctx.height)
    font, lines = _wrap_to_limit(draw, ctx.fonts.sans, text, start, max_width, 3, _px(14, ctx.height))
    disc_font = _font(ctx.fonts.sans, _px(13, ctx.height))
    disc_lines = _wrap(ctx.doc.disclaimer, disc_font, max_width, draw)
    line_h = _text_height(font) + 2
    disc_h = _text_height(disc_font) + 2
    block_h = line_h * len(lines) + 6 + disc_h * len(disc_lines)
    cursor_y = ctx.height - pad // 2 - block_h
    for line in lines:
        draw.text((pad, cursor_y), line, font=font, fill=PAPER)
        cursor_y += line_h
    cursor_y += 4
    for line in disc_lines:
        draw.text((pad, cursor_y), line, font=disc_font, fill=MUTED)
        cursor_y += disc_h


def _label_box(draw, x, y, lines, font, detail_font, fill, anchor, alpha: int) -> None:
    pad = 4
    widths = [draw.textlength(line, font=font) for line in lines]
    line_h = _text_height(font)
    box_w = int(max(widths) + pad * 2)
    box_h = int(line_h * len(lines) + pad * 2)
    if anchor == "center":
        origin_x, origin_y = x - box_w / 2, y - box_h / 2
    else:
        origin_x, origin_y = x, y
    draw.rounded_rectangle(
        [origin_x, origin_y, origin_x + box_w, origin_y + box_h],
        radius=3,
        fill=(*INK, int(200 * alpha / 255)),
    )
    for index, line in enumerate(lines):
        draw.text((origin_x + pad, origin_y + pad + index * line_h), line, font=font, fill=(*fill, alpha))


def _dashed_line(draw, x0, y0, x1, y1, fill, width, dash, gap) -> None:
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy)
    if dist < 1:
        return
    ux, uy = dx / dist, dy / dist
    pos = 0.0
    while pos < dist:
        end = min(dist, pos + dash)
        draw.line(
            [(x0 + ux * pos, y0 + uy * pos), (x0 + ux * end, y0 + uy * end)],
            fill=fill,
            width=width,
        )
        pos = end + gap


def _arrow_head(draw, x0, y0, x1, y1, fill, size) -> None:
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    px, py = -uy, ux
    wing = size * 0.48
    points = [
        (x1, y1),
        (x1 - ux * size + px * wing, y1 - uy * size + py * wing),
        (x1 - ux * size - px * wing, y1 - uy * size - py * wing),
    ]
    draw.polygon(points, fill=fill)


def _wrap_to_limit(draw, font_path, text, start_size, max_width, max_lines, minimum):
    size = start_size
    font = _font(font_path, size)
    lines = _wrap(text, font, max_width, draw)
    while len(lines) > max_lines and size > minimum:
        size -= 1
        font = _font(font_path, size)
        lines = _wrap(text, font, max_width, draw)
    return font, lines


def _wrap(text: str, font, max_width: float, draw) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_font(draw, font_path, text, start_size, max_width, minimum):
    size = start_size
    font = _font(font_path, size)
    while size > minimum and draw.textlength(text, font=font) > max_width:
        size -= 1
        font = _font(font_path, size)
    return font


def _text_height(font) -> int:
    bbox = font.getbbox("Ag")
    return bbox[3] - bbox[1]


def _px(size: int, height: int, minimum: int = 11) -> int:
    return max(minimum, int(round(size * height / 720)))


@functools.lru_cache(maxsize=64)
def _font(path: str, size: int):
    return ImageFont.truetype(path, size)
