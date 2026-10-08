Estimated · not yet built

# Industrial Part Inspection — Capture Rig

A proposed physical setup for running gear_inspector.py on real parts instead of flat photos: a fixed overhead camera, diffuse lighting, and a plain platen feeding the same Python pipeline already built and tested.

Top half: a fixed overhead camera on a boom, ring-lit to keep lighting even (the segmentation step in gear_inspector.py measures color distance from the background, so shadows and glare are the main failure mode to design against). Bottom half: how one captured frame actually moves through the pipeline already built — Python classifies and measures the part, writes gear_params.json, and that file is what gear_train_sim.m already consumes in MATLAB.

**Status:** this is an estimated starting point, not a built or purchased rig — no component has been tested in this configuration. The choices follow directly from constraints the software already has: a plain, evenly-lit background (gear_inspector.py's segmentation assumes one), and a fixed camera distance (so the one-reference-measurement px→mm scale in gear_train_sim.m stays consistent capture to capture). The trigger and output stage are the least settled part — a plain keypress to capture is enough for a prototype; the button/IR sensor and pass-fail LEDs are what it would take to make it feel like a real inspection station instead of a desk setup.