<<<<<<< HEAD
# Animateskill

Skills for AI coding agents that animate silent, subtitled military history.

The user brings a prompt, a script, and sometimes an SVG map or square portraits. The agent plans the war from those inputs, places the map, the armies, and the commanders, burns the script in as subtitles, and renders. Details change with the war. This repo does not ship one fixed battle.

No narration, music, or sound effects. Subtitles are required.

## Skills

| Skill | What it does | Use when |
| --- | --- | --- |
| [historical-animation](skills/historical-animation/SKILL.md) | Plans the film from a prompt and a script, then runs the other skills and the renderer. | Any battle, campaign, or script. |
| [battle-map](skills/battle-map/SKILL.md) | Plate, rivers, mountains, cities, coast, empire colors, changing borders, circular ruler. | Geography and territory. |
| [army-symbols](skills/army-symbols/SKILL.md) | Square army boxes, infantry, cavalry, archers, chariots, elephants, banners. Both sides advance. | Formations and movement. |
| [commander-portraits](skills/commander-portraits/SKILL.md) | Square image to a circular crop, placed beside that army. | Kings, generals, and other named figures. |
| [silent-subtitles](skills/silent-subtitles/SKILL.md) | Burns the user's lines. Keeps the file silent. | Every render. |

Shared rules live in [docs/house-rules.md](docs/house-rules.md). Where each piece sits is in [docs/placement.md](docs/placement.md).

## Quick start

Clone this repo and point your agent at `skills/historical-animation/SKILL.md`.

**OpenCode**

```bash
git clone https://github.com/utkarshdubey2008/Animateskill.git
cd Animateskill
```

`AGENTS.md` maps a battle prompt to these skills.

**Cursor**

```bash
mkdir -p your-project/.cursor/rules
cp skills/historical-animation/SKILL.md your-project/.cursor/rules/historical-animation.md
```

**Gemini CLI**

```bash
gemini skills install https://github.com/utkarshdubey2008/Animateskill.git --path skills
```

**Claude Code**

The slash command is in `.claude/commands/animate.md`.

Renderer setup and the exact commands are in [docs/renderer.md](docs/renderer.md). A 720p film needs Python 3.10, Pillow, FFmpeg, and `rsvg-convert`.

## What an agent produces

A scene plan, an original or user-supplied map, circular commander portraits, army boxes that both advance in the clash, burned subtitles, and a validated silent MP4. The report names the file only after validation prints `result: OK`.
=======
# Animateskill
>>>>>>> origin/main
