"""Documentary JSON schema. Markers are areas. Arrows are the only motion."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCHEMA_VERSION = 1
MARKER_CONFIDENCE = {"attested_area", "approximate"}
ARROW_CONFIDENCE = {"illustrative", "attested"}
ANCHORS = {"n", "s", "e", "w"}
TRANSITIONS = {"cut", "fade", "dissolve"}
EFFECT_TYPES = {"rain", "artillery", "clash"}
OVERLAY_TYPES = {"card"}
MARKS = {"killed", "destroyed", "shattered", "vaporized", "routed"}
SWATCHES = {"solid", "hollow", "dashed"}
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")


@dataclass
class Party:
    name: str
    side: str
    flag: str | None = None
    army_size: str = ""
    killed: str = ""


@dataclass
class Camera:
    cx: float
    cy: float
    zoom: float


@dataclass
class LegendItem:
    swatch: str
    text: str


@dataclass
class MarkerKey:
    t: float
    detail: str | None
    mark: str | None
    alpha: float | None


@dataclass
class MotionKey:
    t: float
    x: float
    y: float


@dataclass
class Motion:
    confidence: str
    keys: list[MotionKey]


@dataclass
class TerritoryLayer:
    id: str
    t: float
    fill: str


@dataclass
class MarkerDef:
    id: str
    label: str
    detail: str
    side: str
    confidence: str
    x: float
    y: float
    anchor: str
    role: str | None = None
    image: Path | None = None
    symbol: list[str] = field(default_factory=list)
    attach: str | None = None
    offset: tuple[float, float] | None = None


@dataclass
class Arrow:
    id: str
    x0: float
    y0: float
    x1: float
    y1: float
    t0: float
    t1: float
    confidence: str
    label: str


@dataclass
class Effect:
    type: str
    t0: float
    t1: float
    marker: str | None
    intensity: float


@dataclass
class Card:
    t0: float
    t1: float
    lines: list[str]
    accent: int


@dataclass
class Scene:
    id: str
    title: str
    start_s: float
    end_s: float
    narration: str
    speech: str
    transition_in: str
    transition_s: float
    camera_start: Camera
    camera_end: Camera
    show: list[str]
    overrides: dict[str, list[MarkerKey]]
    arrows: list[Arrow]
    effects: list[Effect]
    cards: list[Card]
    motions: dict[str, Motion] = field(default_factory=dict)
    layers: list[TerritoryLayer] = field(default_factory=list)


@dataclass
class SourceNote:
    id: str
    text: str
    refs: list[str]


@dataclass
class Documentary:
    id: str
    title: str
    date_label: str
    location_label: str
    fps: int
    width: int
    height: int
    duration_s: float
    disclaimer: str
    legend: list[LegendItem]
    palette: dict[str, tuple[int, int, int]]
    map_svg: Path
    map_attribution: str
    voice: str
    audio_file: Path | None
    markers: dict[str, MarkerDef]
    scenes: list[Scene]
    sources: list[SourceNote]
    parties: list[Party] = field(default_factory=list)
    root: Path = field(default=ROOT)


def frame_count(duration_s: float, fps: int) -> int:
    return int(round(duration_s * fps))


def assign_ranges(scenes: list[Scene], fps: int, nframes: int) -> list[tuple[int, int]]:
    """Half-open frame ranges. The cuts meet, and the last scene ends on nframes."""
    if not scenes:
        raise ValueError("documentary has no scenes")
    bounds = [0]
    for scene in scenes[1:]:
        bounds.append(int(round(scene.start_s * fps)))
    bounds.append(nframes)
    for index in range(1, len(bounds)):
        if bounds[index] <= bounds[index - 1]:
            raise ValueError(f"scene boundary collapsed at {bounds}")
    return list(zip(bounds, bounds[1:]))


def scene_index_at(ranges: list[tuple[int, int]], frame: int) -> int:
    for index, (start, end) in enumerate(ranges):
        if start <= frame < end:
            return index
    return len(ranges) - 1


def local_t(frame: int, start: int, end: int) -> float:
    span = end - start - 1
    if span <= 0:
        return 1.0
    return max(0.0, min(1.0, (frame - start) / span))


def load_documentary(path: Path) -> Documentary:
    raw_path = Path(path)
    try:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{raw_path}: invalid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{raw_path}: documentary must be a JSON object")
    where = str(raw_path)
    _reject_unknown(
        data,
        {
            "schema_version",
            "id",
            "title",
            "date_label",
            "location_label",
            "fps",
            "width",
            "height",
            "duration_s",
            "disclaimer",
            "legend",
            "palette",
            "map",
            "narration",
            "markers",
            "scenes",
            "sources",
            "parties",
        },
        where,
    )
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"{where}: unsupported schema_version {version}")
    doc_id = _string(data, "id", where)
    if not SLUG.fullmatch(doc_id):
        raise ValueError(f"{where}: id must be a lowercase slug")
    width = _int(data, "width", where)
    height = _int(data, "height", where)
    fps = _int(data, "fps", where)
    if width % 2 or height % 2:
        raise ValueError(f"{where}: width and height must be even")
    if width < 160 or height < 90:
        raise ValueError(f"{where}: frame size is too small")
    if fps < 1 or fps > 60:
        raise ValueError(f"{where}: fps must be from 1 to 60")
    duration_s = _number(data, "duration_s", where)
    if duration_s <= 0:
        raise ValueError(f"{where}: duration_s must be positive")

    map_obj = _object(data, "map", where)
    _reject_unknown(map_obj, {"svg", "attribution"}, f"{where}.map")
    svg_rel = _string(map_obj, "svg", f"{where}.map")
    map_svg = _resolve(svg_rel)
    attribution = _string(map_obj, "attribution", f"{where}.map")

    narration = _object(data, "narration", where)
    _reject_unknown(narration, {"voice", "audio_file"}, f"{where}.narration")
    voice = _string(narration, "voice", f"{where}.narration")
    audio_value = narration.get("audio_file")
    audio_file: Path | None
    if audio_value in (None, ""):
        audio_file = None
    else:
        if not isinstance(audio_value, str):
            raise ValueError(f"{where}.narration.audio_file must be a string or null")
        audio_file = _resolve(audio_value)

    palette = _palette(_object(data, "palette", where), f"{where}.palette")
    markers = _markers(_object(data, "markers", where), palette, f"{where}.markers")
    legend = _legend(data.get("legend"), f"{where}.legend")
    scenes = _scenes(data.get("scenes"), markers, f"{where}.scenes")
    _check_timeline(scenes, duration_s, where)
    sources = _sources(data.get("sources"), f"{where}.sources")
    parties_raw = data.get("parties", [])
    parties: list[Party] = []
    if isinstance(parties_raw, list):
        for idx, item in enumerate(parties_raw):
            spot = f"{where}.parties[{idx}]"
            if isinstance(item, dict):
                parties.append(
                    Party(
                        name=_string(item, "name", spot),
                        side=_string(item, "side", spot),
                        flag=item.get("flag"),
                        army_size=str(item.get("army_size", "")),
                        killed=str(item.get("killed", "")),
                    )
                )

    return Documentary(
        id=doc_id,
        title=_string(data, "title", where),
        date_label=_string(data, "date_label", where),
        location_label=_string(data, "location_label", where),
        fps=fps,
        width=width,
        height=height,
        duration_s=duration_s,
        disclaimer=_string(data, "disclaimer", where),
        legend=legend,
        palette=palette,
        map_svg=map_svg,
        map_attribution=attribution,
        voice=voice,
        audio_file=audio_file,
        markers=markers,
        scenes=scenes,
        sources=sources,
        parties=parties,
        root=ROOT,
    )


def _check_timeline(scenes: list[Scene], duration_s: float, where: str) -> None:
    if not scenes:
        raise ValueError(f"{where}: at least one scene is required")
    if abs(scenes[0].start_s) > 1e-6:
        raise ValueError(f"{where}: first scene must start at 0")
    if abs(scenes[-1].end_s - duration_s) > 1e-3:
        raise ValueError(f"{where}: last scene must end at duration_s")
    for earlier, later in zip(scenes, scenes[1:]):
        if abs(earlier.end_s - later.start_s) > 1e-3:
            raise ValueError(
                f"{where}: gap or overlap between {earlier.id} and {later.id}"
            )
        if later.end_s <= later.start_s:
            raise ValueError(f"{where}.{later.id}: scene duration must be positive")


def _scenes(value: object, markers: dict[str, MarkerDef], where: str) -> list[Scene]:
    if not isinstance(value, list):
        raise ValueError(f"{where} must be a list")
    scenes: list[Scene] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        spot = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(
            item,
            {
                "id",
                "title",
                "start_s",
                "end_s",
                "narration",
                "speech",
                "transition_in",
                "transition_s",
                "camera",
                "show",
                "overrides",
                "arrows",
                "effects",
                "overlays",
                "motions",
                "layers",
            },
            spot,
        )
        scene_id = _string(item, "id", spot)
        if scene_id in seen:
            raise ValueError(f"{spot}: duplicate scene id {scene_id}")
        seen.add(scene_id)
        transition = _string(item, "transition_in", spot)
        if transition not in TRANSITIONS:
            raise ValueError(f"{spot}.transition_in must be one of {sorted(TRANSITIONS)}")
        camera = _object(item, "camera", spot)
        _reject_unknown(camera, {"start", "end"}, f"{spot}.camera")
        show = item.get("show")
        if not isinstance(show, list) or not all(isinstance(name, str) for name in show):
            raise ValueError(f"{spot}.show must be a list of marker ids")
        for name in show:
            if name not in markers:
                raise ValueError(f"{spot}.show references unknown marker {name}")
        overrides = _overrides(item.get("overrides", {}), set(show), f"{spot}.overrides")
        scenes.append(
            Scene(
                id=scene_id,
                title=_string(item, "title", spot),
                start_s=_number(item, "start_s", spot),
                end_s=_number(item, "end_s", spot),
                narration=_string(item, "narration", spot),
                speech=_string(item, "speech", spot),
                transition_in=transition,
                transition_s=_number(item, "transition_s", spot),
                camera_start=_camera(camera.get("start"), f"{spot}.camera.start"),
                camera_end=_camera(camera.get("end"), f"{spot}.camera.end"),
                show=list(show),
                overrides=overrides,
                arrows=_arrows(item.get("arrows", []), f"{spot}.arrows"),
                effects=_effects(item.get("effects", []), markers, f"{spot}.effects"),
                cards=_cards(item.get("overlays", []), f"{spot}.overlays"),
                motions=_motions(item.get("motions"), markers, f"{spot}.motions"),
                layers=_layers(item.get("layers"), f"{spot}.layers"),
            )
        )
    return scenes


def _camera(value: object, where: str) -> Camera:
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be an object")
    _reject_unknown(value, {"cx", "cy", "zoom"}, where)
    cx = _number(value, "cx", where)
    cy = _number(value, "cy", where)
    zoom = _number(value, "zoom", where)
    if not 0.0 <= cx <= 1.0 or not 0.0 <= cy <= 1.0:
        raise ValueError(f"{where}: cx and cy must be from 0 to 1")
    if not 0.2 <= zoom <= 1.0:
        raise ValueError(f"{where}: zoom must be from 0.2 to 1")
    return Camera(cx, cy, zoom)


def _overrides(
    value: object, shown: set[str], where: str
) -> dict[str, list[MarkerKey]]:
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be an object")
    parsed: dict[str, list[MarkerKey]] = {}
    for marker_id, spec in value.items():
        spot = f"{where}.{marker_id}"
        if marker_id not in shown:
            raise ValueError(f"{spot}: override is for a marker this scene does not show")
        if not isinstance(spec, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(spec, {"keys"}, spot)
        keys_raw = spec.get("keys", [])
        if not isinstance(keys_raw, list) or not keys_raw:
            raise ValueError(f"{spot}.keys must be a non-empty list")
        keys: list[MarkerKey] = []
        for index, key in enumerate(keys_raw):
            key_where = f"{spot}.keys[{index}]"
            if not isinstance(key, dict):
                raise ValueError(f"{key_where} must be an object")
            _reject_unknown(key, {"t", "detail", "mark", "alpha"}, key_where)
            mark = key.get("mark")
            if mark is not None:
                if not isinstance(mark, str) or mark not in MARKS:
                    raise ValueError(f"{key_where}.mark must be one of {sorted(MARKS)}")
            detail = key.get("detail")
            if detail is not None and not isinstance(detail, str):
                raise ValueError(f"{key_where}.detail must be a string")
            alpha = None if "alpha" not in key else key["alpha"]
            if alpha is not None:
                alpha = _as_number(alpha, f"{key_where}.alpha")
                if not 0.0 <= alpha <= 1.0:
                    raise ValueError(f"{key_where}.alpha must be from 0 to 1")
            keys.append(
                MarkerKey(
                    t=_as_unit(_as_number(key.get("t"), f"{key_where}.t"), f"{key_where}.t"),
                    detail=detail,
                    mark=mark,
                    alpha=alpha,
                )
            )
        keys.sort(key=lambda item: item.t)
        parsed[marker_id] = keys
    return parsed


def _arrows(value: object, where: str) -> list[Arrow]:
    if not isinstance(value, list):
        raise ValueError(f"{where} must be a list")
    arrows: list[Arrow] = []
    for index, item in enumerate(value):
        spot = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(
            item,
            {"id", "from", "to", "t0", "t1", "confidence", "label"},
            spot,
        )
        confidence = _string(item, "confidence", spot)
        if confidence not in ARROW_CONFIDENCE:
            raise ValueError(f"{spot}.confidence must be one of {sorted(ARROW_CONFIDENCE)}")
        x0, y0 = _point(item.get("from"), f"{spot}.from")
        x1, y1 = _point(item.get("to"), f"{spot}.to")
        t0 = _as_unit(_number(item, "t0", spot), f"{spot}.t0")
        t1 = _as_unit(_number(item, "t1", spot), f"{spot}.t1")
        if t1 <= t0:
            raise ValueError(f"{spot}: t1 must be greater than t0")
        arrows.append(
            Arrow(
                id=_string(item, "id", spot),
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                t0=t0,
                t1=t1,
                confidence=confidence,
                label=_string(item, "label", spot),
            )
        )
    return arrows


def _effects(value: object, markers: dict[str, MarkerDef], where: str) -> list[Effect]:
    if not isinstance(value, list):
        raise ValueError(f"{where} must be a list")
    effects: list[Effect] = []
    for index, item in enumerate(value):
        spot = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(item, {"type", "t0", "t1", "marker", "intensity"}, spot)
        kind = _string(item, "type", spot)
        if kind not in EFFECT_TYPES:
            raise ValueError(f"{spot}.type must be one of {sorted(EFFECT_TYPES)}")
        marker = item.get("marker")
        if kind in ("artillery", "clash"):
            if not isinstance(marker, str) or marker not in markers:
                raise ValueError(f"{spot}: {kind} requires a known marker")
        elif marker not in (None,):
            raise ValueError(f"{spot}: rain does not take a marker")
        t0 = _as_unit(_number(item, "t0", spot), f"{spot}.t0")
        t1 = _as_unit(_number(item, "t1", spot), f"{spot}.t1")
        if t1 <= t0:
            raise ValueError(f"{spot}: t1 must be greater than t0")
        intensity = float(item.get("intensity", 1))
        if isinstance(item.get("intensity", 1), bool) or not isinstance(item.get("intensity", 1), (int, float)):
            raise ValueError(f"{spot}.intensity must be a number")
        if not 0.0 < intensity <= 1.0:
            raise ValueError(f"{spot}.intensity must be from 0 to 1")
        effects.append(Effect(kind, t0, t1, marker if isinstance(marker, str) else None, float(intensity)))
    return effects


def _cards(value: object, where: str) -> list[Card]:
    if not isinstance(value, list):
        raise ValueError(f"{where} must be a list")
    cards: list[Card] = []
    for index, item in enumerate(value):
        spot = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(item, {"type", "t0", "t1", "lines", "accent"}, spot)
        kind = _string(item, "type", spot)
        if kind not in OVERLAY_TYPES:
            raise ValueError(f"{spot}.type must be one of {sorted(OVERLAY_TYPES)}")
        lines = item.get("lines")
        if not isinstance(lines, list) or not lines or not all(isinstance(line, str) and line for line in lines):
            raise ValueError(f"{spot}.lines must be a non-empty list of strings")
        accent = item.get("accent", 0)
        if isinstance(accent, bool) or not isinstance(accent, int):
            raise ValueError(f"{spot}.accent must be an integer")
        if not 0 <= accent < len(lines):
            raise ValueError(f"{spot}.accent is outside the line list")
        t0 = _as_unit(_number(item, "t0", spot), f"{spot}.t0")
        t1 = _as_unit(_number(item, "t1", spot), f"{spot}.t1")
        if t1 <= t0:
            raise ValueError(f"{spot}: t1 must be greater than t0")
        cards.append(Card(t0, t1, list(lines), accent))
    return cards


def _motions(value: object, markers: dict[str, MarkerDef], where: str) -> dict[str, Motion]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be an object")
    result: dict[str, Motion] = {}
    for marker_id, motion_obj in value.items():
        spot = f"{where}.{marker_id}"
        if marker_id not in markers:
            raise ValueError(f"{spot}: unknown marker {marker_id}")
        if not isinstance(motion_obj, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(motion_obj, {"confidence", "keys"}, spot)
        conf = _string(motion_obj, "confidence", spot)
        if conf not in ARROW_CONFIDENCE:
            raise ValueError(f"{spot}.confidence must be one of {sorted(ARROW_CONFIDENCE)}")
        raw_keys = motion_obj.get("keys")
        if not isinstance(raw_keys, list) or not raw_keys:
            raise ValueError(f"{spot}.keys must be a non-empty list")
        keys: list[MotionKey] = []
        for k_idx, k_item in enumerate(raw_keys):
            k_spot = f"{spot}.keys[{k_idx}]"
            if not isinstance(k_item, dict):
                raise ValueError(f"{k_spot} must be an object")
            _reject_unknown(k_item, {"t", "x", "y"}, k_spot)
            t = _as_unit(_number(k_item, "t", k_spot), f"{k_spot}.t")
            x = _as_unit(_number(k_item, "x", k_spot), f"{k_spot}.x")
            y = _as_unit(_number(k_item, "y", k_spot), f"{k_spot}.y")
            keys.append(MotionKey(t=t, x=x, y=y))
        keys.sort(key=lambda k: k.t)
        result[marker_id] = Motion(confidence=conf, keys=keys)
    return result


def _layers(value: object, where: str) -> list[TerritoryLayer]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{where} must be a list")
    layers: list[TerritoryLayer] = []
    for index, item in enumerate(value):
        spot = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(item, {"id", "t", "fill"}, spot)
        lid = _string(item, "id", spot)
        t = _as_unit(_number(item, "t", spot), f"{spot}.t")
        fill = _string(item, "fill", spot)
        layers.append(TerritoryLayer(id=lid, t=t, fill=fill))
    return layers


def _markers(value: dict, palette: dict[str, tuple[int, int, int]], where: str) -> dict[str, MarkerDef]:
    markers: dict[str, MarkerDef] = {}
    for marker_id, item in value.items():
        spot = f"{where}.{marker_id}"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(
            item,
            {
                "label",
                "detail",
                "side",
                "confidence",
                "x",
                "y",
                "anchor",
                "role",
                "image",
                "symbol",
                "symbols",
                "attach",
                "offset",
            },
            spot,
        )
        side = _string(item, "side", spot)
        if side not in palette:
            raise ValueError(f"{spot}.side {side} has no palette entry")
        confidence = _string(item, "confidence", spot)
        if confidence not in MARKER_CONFIDENCE:
            raise ValueError(f"{spot}.confidence must be one of {sorted(MARKER_CONFIDENCE)}")
        anchor = _string(item, "anchor", spot)
        if anchor not in ANCHORS:
            raise ValueError(f"{spot}.anchor must be one of {sorted(ANCHORS)}")
        x = _as_unit(_number(item, "x", spot), f"{spot}.x")
        y = _as_unit(_number(item, "y", spot), f"{spot}.y")
        role = item.get("role")
        if role is not None and role not in {"person", "army"}:
            raise ValueError(f"{spot}.role must be 'person' or 'army'")
        image_val = item.get("image")
        image_path: Path | None = None
        if image_val is not None:
            if not isinstance(image_val, str):
                raise ValueError(f"{spot}.image must be a string path or null")
            image_path = _resolve(image_val)
        symbols: list[str] = []
        sym_val = item.get("symbol") if "symbol" in item else item.get("symbols")
        if sym_val is not None:
            if isinstance(sym_val, str):
                symbols = [sym_val]
            elif isinstance(sym_val, list) and all(isinstance(s, str) for s in sym_val):
                symbols = list(sym_val)
            else:
                raise ValueError(f"{spot}.symbol must be a string or list of strings")
            valid_syms = {"infantry", "cavalry", "archer", "chariot", "elephant"}
            for s in symbols:
                if s not in valid_syms:
                    raise ValueError(f"{spot}.symbol contains invalid symbol '{s}'")
        attach = item.get("attach")
        if attach is not None and not isinstance(attach, str):
            raise ValueError(f"{spot}.attach must be a string marker id")
        offset_val = item.get("offset")
        offset: tuple[float, float] | None = None
        if offset_val is not None:
            if not isinstance(offset_val, (list, tuple)) or len(offset_val) != 2:
                raise ValueError(f"{spot}.offset must be a [dx, dy] list")
            offset = (_as_number(offset_val[0], f"{spot}.offset[0]"), _as_number(offset_val[1], f"{spot}.offset[1]"))
        detail_val = item.get("detail", "")
        if not isinstance(detail_val, str):
            raise ValueError(f"{spot}.detail must be a string")
        markers[marker_id] = MarkerDef(
            id=marker_id,
            label=_string(item, "label", spot),
            detail=detail_val,
            side=side,
            confidence=confidence,
            x=x,
            y=y,
            anchor=anchor,
            role=role,
            image=image_path,
            symbol=symbols,
            attach=attach,
            offset=offset,
        )
    if not markers:
        raise ValueError(f"{where} must define at least one marker")
    return markers


def _legend(value: object, where: str) -> list[LegendItem]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{where} must be a non-empty list")
    items: list[LegendItem] = []
    for index, item in enumerate(value):
        spot = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(item, {"swatch", "text"}, spot)
        swatch = _string(item, "swatch", spot)
        if swatch not in SWATCHES:
            raise ValueError(f"{spot}.swatch must be one of {sorted(SWATCHES)}")
        items.append(LegendItem(swatch, _string(item, "text", spot)))
    return items


def _sources(value: object, where: str) -> list[SourceNote]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{where} must be a non-empty list")
    notes: list[SourceNote] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        spot = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{spot} must be an object")
        _reject_unknown(item, {"id", "text", "refs"}, spot)
        note_id = _string(item, "id", spot)
        if note_id in seen:
            raise ValueError(f"{spot}: duplicate source id {note_id}")
        seen.add(note_id)
        refs = item.get("refs")
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref for ref in refs):
            raise ValueError(f"{spot}.refs must be a non-empty list of strings")
        notes.append(SourceNote(note_id, _string(item, "text", spot), list(refs)))
    return notes


def _palette(value: dict, where: str) -> dict[str, tuple[int, int, int]]:
    if not value:
        raise ValueError(f"{where} must not be empty")
    parsed: dict[str, tuple[int, int, int]] = {}
    for name, color in value.items():
        if not isinstance(color, str):
            raise ValueError(f"{where}.{name} must be a hex color")
        parsed[name] = _hex_rgb(color, f"{where}.{name}")
    return parsed


def _hex_rgb(value: str, where: str) -> tuple[int, int, int]:
    text = value.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6 or any(char not in "0123456789abcdefABCDEF" for char in text):
        raise ValueError(f"{where} must be a #RRGGBB color")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def _point(value: object, where: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{where} must be [x, y]")
    x = _as_unit(_as_number(value[0], f"{where}[0]"), f"{where}[0]")
    y = _as_unit(_as_number(value[1], f"{where}[1]"), f"{where}[1]")
    return x, y


def _resolve(rel: str) -> Path:
    candidate = Path(rel)
    if candidate.is_file():
        return candidate.resolve()
    rooted = ROOT / rel
    if rooted.is_file():
        return rooted.resolve()
    raise ValueError(f"asset not found: {rel}")


def _reject_unknown(obj: dict, allowed: set[str], where: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"{where}: unknown fields: {names}")


def _object(data: dict, key: str, where: str) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{where}.{key} must be an object")
    return value


def _string(data: dict, key: str, where: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.{key} must be a non-empty string")
    return value


def _number(data: dict, key: str, where: str) -> float:
    if key not in data:
        raise ValueError(f"{where}.{key} is required")
    return _as_number(data[key], f"{where}.{key}")


def _int(data: dict, key: str, where: str) -> int:
    value = _number(data, key, where)
    if int(value) != value:
        raise ValueError(f"{where}.{key} must be an integer")
    return int(value)


def _as_number(value: object, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where} must be a number")
    return float(value)


def _as_unit(value: float, where: str) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{where} must be from 0 to 1")
    return value
