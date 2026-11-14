# AI in Drug Discovery

Code that accompanies the **WhiskerBrief "AI in Drug Discovery"** video course. Every video has its own folder (`part-NN-…`) holding the code used in that video. Shared tooling lives in `shared/`.

| Part | Video | Folder |
|------|-------|--------|
| 1 | Can AI simulate a cell? | [`part-01-can-ai-simulate-a-cell`](part-01-can-ai-simulate-a-cell) |
| 2 | Microscopy: from cells to organoids and tissues | [`part-02-microscopy-cells-to-organoids-and-tissues`](part-02-microscopy-cells-to-organoids-and-tissues) |
| 3 | _coming soon_ | – |
| 4 | _coming soon_ | – |
| 5 | _coming soon_ | – |

## Layout

```
part-NN-<video-name>/
  README.md        what the video covers and what each folder contains
  animation/       the scene code that draws the animated explainer visuals
shared/
  animation-kit/   the drawing kit, timing/cue tools and renderer used by every part
```

## Notes

- The animation scenes are small HTML/SVG pages driven by a time cue file (`cues.json`) that follows the narration. They are rendered to video frame by frame with `shared/animation-kit/lib/render.py` (Chrome + Playwright, then ffmpeg).
- Some scripts still use the absolute paths of the machine they were built on (for example `/home/claude/work`). Change those paths to your own checkout before running them.
- Rendered videos, audio and large data files are not stored here (see `.gitignore`).
