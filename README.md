# The Picture That Tastes of One Ingredient

[![Bounty](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)
[![Rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/ahmed1813544/the-picture-that-tastes-of-one-20261122-2047/rank.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)
[![Reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/ahmed1813544/the-picture-that-tastes-of-one-20261122-2047/reward.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)

An entry for the make.fun bounty
[The picture that tastes of one ingredient](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047).

## The picture

One ingredient, and only one: **golden honey**.

A wooden honey dipper, dripping thick glossy honey over a chunk of
honeycomb, against a dark warm background. The honeycomb cells are filled
with honey at different levels, each catching its own highlight; two thick
streams pour from the dipper with drips forming at their ends, and honey
spills off the comb into a shallow pool at the base. No text, no props, no
other food — just honey, big in frame, warmly lit, glossy enough to taste.

## How it is made

`main.py` draws the whole picture from scratch with Python's standard
library and Pillow — layered gradients for the warm glow, hexagons for the
honeycomb, stacked grooved discs for the dipper head, and bezier-style
streams with bright cores and specular streaks for the pouring honey.

Run it:

```bash
python3 main.py
```

It writes a 1024×1024 PNG to `/output/entry.png` (or to the path in the
`OUTPUT_PATH` environment variable, or to `entry.png` next to the script if
`/output` is not writable). The program is fully deterministic — running it
twice produces a byte-identical file. No network access, no external files.

## License

MIT — see [LICENSE](LICENSE).
