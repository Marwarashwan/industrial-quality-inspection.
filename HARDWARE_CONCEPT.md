# Hardware Concept: Inspection Capture Rig

**Status: estimated, not built.** This is a proposed physical setup for running `gear_inspector.py` on real parts under a camera, instead of flat reference photos. No component has been purchased or tested in this configuration — it's a reasonable starting point derived from constraints the software already has, not a validated design.

## Why this exists

Everything built so far — detection, classification, bore/tooth measurement, the MATLAB simulation — runs on still photos. This is what a physical capture station would need to look like to put a real part under the camera and get the same pipeline to run on it automatically.

## Layout

```
                 ring light
                      ⌒
          ┌───────────┴───────────┐
          │        camera         │   fixed boom, overhead,
          └───────────┬───────────┘   constant focal distance
                       │
                       ▼
          ┌─────────────────────┐
          │  inspection platen  │  ← part placed here
          └─────────────────────┘
                                   [ trigger ]  button / IR sensor
```

## Components

| Component | Choice | Why |
|---|---|---|
| **Camera** | USB webcam or Raspberry Pi Camera Module, fixed overhead on a boom | `gear_inspector.py` expects a roughly top-down view. A *fixed* mount matters more than the camera itself — the px→mm scale in `gear_train_sim.m` comes from one reference measurement, so the distance from lens to platen has to stay constant between captures. |
| **Lighting** | Diffuse ring light around the lens | Segmentation (`segment_foreground()`) works by measuring color distance from the background in LAB space. Shadows and glare read as false edges — even, shadow-free lighting is what the algorithm actually needs, more than brightness. |
| **Platen** | Plain, matte, light-colored surface | Directly tied to a bug already hit and fixed during testing: a gray (230,230,230) background got merged with the padding border and misread as one giant object. A clean, consistently light background is a hardware requirement, not just a nice-to-have. |
| **Trigger** | Pushbutton or IR/photoelectric sensor | Fires a capture when a part is placed, instead of a person pressing a key. Simplest working version: just a keypress — the sensor is what turns this from a desk setup into something that feels like a real inspection station. |
| **Compute** | Raspberry Pi 4/5, or a small PC/laptop | Runs `gear_inspector.py` as-is — pure Python/OpenCV, no GPU needed. A Pi keeps the whole rig small and cheap; a laptop is the simpler path for a first prototype. |
| **Output** | Small screen or terminal + pass/fail LEDs | Shows the classification and measurement immediately. LEDs (green = confident pass, yellow = unsure, red = non-object) make the result readable from across a room, the way a real shop-floor station would need to be. |

## Data flow

1. Trigger fires → camera captures one still frame.
2. Frame goes to the compute unit over USB (webcam) or CSI (Pi Camera).
3. `gear_inspector.py` runs its existing pipeline: segmentation → classification → measurement.
4. Result shows on the output stage (screen/LEDs) **and** gets written to `gear_params.json` — the exact same file the pipeline already produces from a folder of photos.
5. `gear_params.json` hands off to `gear_train_sim.m` in MATLAB, unchanged from how it already works.

Nothing about the software pipeline needs to change for this — the rig's whole job is to reliably produce the same kind of clean, top-down, evenly-lit photo the software was already built and tested against.

## What's least settled

The trigger and output stage are the roughest part of this estimate. A plain keypress-to-capture is enough to prove the rig works at all; the physical button/sensor and the pass/fail LED readout are what would turn it into something a non-technical person could actually use on a bench, which is the real point of a hardware version of this project.
