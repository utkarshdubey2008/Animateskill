# Contributing

Skills in this repo teach an agent to animate a war it has not seen before.

## A skill is ready when

- The description says when to use it, in words a user would actually type.
- The steps are enough to act without rereading the chat that created the skill.
- Rules that already live in `docs/` are linked, not copied.
- It keeps the film silent and the user's script on screen.
- An example, if you add one, is marked as a sample and tells the agent to replace every name for a new war.

## Layout

```
skills/<name>/SKILL.md
skills/<name>/examples.md     optional
skills/<name>/assets/         optional SVG symbols
skills/<name>/scripts/        optional tools
```

Run `python3 -m unittest tests.test_engine tests.test_circular_crop -v` before you push. Do not commit `output/` renders, caches, or credentials.
