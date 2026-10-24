"""Palettes for compose.py: one module per sound, all answering the same section grammar and cue types.

A palette module defines NAME, PURPOSE (what kind of video it fits), BPM (its natural tempo) and:
  setup(ctx)                                   load samples; fall back to synthesis when a sample is missing
  intro(ctx, a, b)                             no rhythm: a pad or drone
  groove(ctx, a, b, e, back=True, hats=True, keys=True)
                                               the groove at energy e; back = backbeat, hats = top percussion,
                                               keys = the melodic figure (compose turns them off for tease/light/muffled)
  build(ctx, a, b)                             a crescendo that lands on b
  stop(ctx, a, b)                              drums out: a held pad and at most a slow pulse
  riser(ctx, a, b)                             a riser that ends on b
  cue(ctx, c) -> bool                          the sound for one cue; False lets compose use its default
  emphasis(ctx, t, level)                      a short, bright accent the sync gate adds where a cue was not heard
"""
