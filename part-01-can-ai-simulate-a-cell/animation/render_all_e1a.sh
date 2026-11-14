#!/bin/bash
cd /home/claude/work
python3 lib/render.py scenes/e1_loss_intuition/scene.html --cues scenes/e1_loss_intuition/cues.json --frames 961 --out out/e1_li --name scene
python3 lib/render.py scenes/e1_loss/scene.html --cues scenes/e1_loss/cues.json --frames 2053 --out out/e1_loss --name scene
python3 lib/render.py scenes/e1_loss_example/scene.html --cues scenes/e1_loss_example/cues.json --frames 889 --out out/e1_le --name scene
