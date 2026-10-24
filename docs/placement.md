# Where everything sits

Read this before placing a map label, an army, a portrait, or the ruler. Coordinates are the ones in `docs/house-rules.md`.

## Frame

| Zone | What lives there |
| --- | --- |
| Top left | Film title, scene title, legend. Leave this corner of the map empty of place names. |
| Top right | Date. |
| Center | The two armies and the ground between them. |
| Bottom 20% | Subtitles, then the one-line disclaimer. No unit icon and no portrait label in this band. |
| Wide-shot corner, clear of both bands | The circular ruler. On a 1600×900 plate put it near viewBox `(1480, 150)`. It may clip on a tight zoom. |

## Map plate

Use the user's SVG when they provide a map they can use. Otherwise draw an original 1600×900 schematic.

Draw, in this order, underneath the armies:

1. Sea or a pale outer ground, then the land.
2. Coastline, rivers, and a simple mountain mark where the sources put high ground.
3. Cities as small squares with short names.
4. Empire territories as flat fills. One color per empire, reused on that empire's banner and army box.
5. Roads only when a route is part of the story.

Place-name labels sit in the upper two-thirds, with a dark halo so they survive the fill. Long labels collide. Use the short name, and `approx.` when the spot is traditional.

The plate does not contain troop arrows or unit icons. Those are scene objects, so they can move.

## Territories

Each region is its own SVG path with a stable id, grouped by the empire that holds it at the start:

```xml
<g id="held-by-north" fill="#8a3a32">
  <path id="region-example" d="..."/>
</g>
```

When a cited treaty cedes a region, that path changes to the other empire's fill at that scene's time. Do not recolor a region the sources do not hand over. If the list of ceded lands is debated, color only the lands the source you cite actually names, and say the rest is disputed in `sources`.

The renderer ships with one map per film. A border change means extending it with the optional `layers` field in `docs/scene-contract.md` before you render that shot.

## The two armies

Pick the axis from the geography. If one camp is north of the other, the front runs east-west and both armies move along north-south. If a river splits them east and west, the front runs north-south and both move along east-west. Do not reuse another film's axis.

| Piece | Where |
| --- | --- |
| Army | A square box in that empire's color. About 0.08 by 0.08 of the map. Attested ground is a filled box. Approximate ground is a hollow box. |
| Unit symbols | A row inside the box: infantry, cavalry, archers, chariots, elephants. Only the arms the sources give that force. One icon is a formation, not one man. |
| Banner | On the enemy-facing edge of the box. |
| Commander | A circle just outside the box, on the home side, about 0.045 of the map away so the circle does not cover the icons. |
| The other commander | The same, mirrored, on the far side of the gap. |
| Gap | At least 0.06 of the map between the two boxes at the closest frame. They never overlap. |
| A force that does not fight | Off to the flank, not on the axis. It does not advance. |

During the clash scene both boxes move forward, toward the gap, and stop short of it. The commander circle is attached to its box, so it keeps the same offset while the box moves. A dashed trail behind each box is labeled `Illustrative advance`.

Suggested timing inside the clash scene: hold until `t` 0.12, arrive by `t` 0.82. Later scenes that still show those armies start them where the previous scene left them, or the dissolve jumps.

Paint order inside a scene: territory and plate, then trails, then army boxes, then unit symbols, then commander circles, then labels.

## Circular ruler

`skills/battle-map/assets/circular-ruler.svg` is a compass ring. North is the marked arm. It is not a measured scale and not a survey. Do not print a distance on it unless a cited source gives that scale.

## Portraits

The user supplies a square image. Crop it with `skills/commander-portraits/scripts/circular_crop.py`. The face stays centered. The ring uses the empire color.

If they have not supplied a file, draw the circle in the empire color with the commander's initials and the detail `portrait not supplied`. Do not generate a face.

Detail text is one of: `coin`, `sculpture`, `artistic reconstruction`.

## Subtitles and disclaimer

The subtitle is the user's line, bottom left, at most two lines. The disclaimer sits under it in smaller type: `Schematic, not a survey.` Add the river or the century when that is what a viewer could mistake.
