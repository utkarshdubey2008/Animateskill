"""Camera math and easing. No image library, so the tests stay small."""

from __future__ import annotations


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def pulse(t: float, t0: float, t1: float, ramp: float = 0.05) -> float:
    """Strength inside [t0, t1]. Ramps stay inside the window."""
    if t < t0 or t > t1 or t1 <= t0:
        return 0.0
    ramp = min(ramp, (t1 - t0) / 2.0)
    if ramp <= 1e-9:
        return 1.0
    if t < t0 + ramp:
        return (t - t0) / ramp
    if t > t1 - ramp:
        return (t1 - t) / ramp
    return 1.0


def camera_window(
    cx: float,
    cy: float,
    zoom: float,
    map_w: int,
    map_h: int,
    aspect: float,
) -> tuple[float, float, float, float]:
    """Visible map window in pixels: left, top, width, height.

    `zoom` is the fraction of map width in frame. The window matches the
    output aspect and is clamped onto the plate.
    """
    if zoom <= 0:
        raise ValueError("zoom must be positive")
    if aspect <= 0:
        raise ValueError("aspect must be positive")
    view_w = map_w * zoom
    view_h = view_w / aspect
    if view_h > map_h:
        view_h = float(map_h)
        view_w = view_h * aspect
    if view_w > map_w:
        view_w = float(map_w)
        view_h = view_w / aspect
    left = cx * map_w - view_w / 2.0
    top = cy * map_h - view_h / 2.0
    left = clamp(left, 0.0, max(0.0, map_w - view_w))
    top = clamp(top, 0.0, max(0.0, map_h - view_h))
    return left, top, view_w, view_h


def crop_box(
    window: tuple[float, float, float, float],
    map_w: int,
    map_h: int,
) -> tuple[int, int, int, int]:
    """Integer Pillow crop box covering `window`."""
    left, top, view_w, view_h = window
    box_l = int(round(left))
    box_t = int(round(top))
    box_r = int(round(left + view_w))
    box_b = int(round(top + view_h))
    if box_r - box_l < 2:
        box_r = box_l + 2
    if box_b - box_t < 2:
        box_b = box_t + 2
    if box_r > map_w:
        box_l -= box_r - map_w
        box_r = map_w
    if box_b > map_h:
        box_t -= box_b - map_h
        box_b = map_h
    box_l = max(0, box_l)
    box_t = max(0, box_t)
    box_r = min(map_w, max(box_r, box_l + 2))
    box_b = min(map_h, max(box_b, box_t + 2))
    return box_l, box_t, box_r, box_b


def project(
    x: float,
    y: float,
    box: tuple[int, int, int, int],
    out_w: int,
    out_h: int,
    map_w: int,
    map_h: int,
) -> tuple[float, float]:
    """Project a normalized map point through the same crop as the plate."""
    box_l, box_t, box_r, box_b = box
    sx = (x * map_w - box_l) / float(box_r - box_l) * out_w
    sy = (y * map_h - box_t) / float(box_b - box_t) * out_h
    return sx, sy
