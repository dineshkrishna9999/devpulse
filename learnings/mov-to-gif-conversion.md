# Learnings

Things I learned while building FirstToKnow. Keeping these here so I (and anyone contributing) don't have to re-Google them.

---

## Converting .mov to GIF with ffmpeg (for README demos)

GitHub READMEs can't embed `.mov` or `.mp4` — but GIFs autoplay, which makes them perfect for demo screenshots that grab attention.

### The command

```bash
ffmpeg -i example.mov \
  -vf "fps=12,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3" \
  -loop 0 demo.gif
```

### What each part does

| Part | What it does |
|------|-------------|
| `-i example.mov` | Input file |
| `fps=12` | Reduces frame rate to 12fps — GIFs don't need high FPS, and this massively cuts file size |
| `scale=800:-1` | Scales width to 800px, auto-calculates height to keep aspect ratio |
| `flags=lanczos` | High-quality downscaling algorithm (sharper than default bilinear) |
| `split[s0][s1]` | Splits video into two copies for the two-pass palette trick (see below) |
| `palettegen=max_colors=128:stats_mode=diff` | **Pass 1:** Analyzes all frames to find the best 128 colors. `stats_mode=diff` only looks at pixels that change between frames — perfect for terminal recordings |
| `paletteuse=dither=bayer:bayer_scale=3` | **Pass 2:** Renders the GIF using the optimized palette with Bayer dithering to simulate missing colors |
| `-loop 0` | Loop forever (0 = infinite) |

### Why the palette trick matters

GIF only supports 256 colors. Without palette optimization, ffmpeg uses a generic palette and the result looks washed out and is bigger. The two-pass approach:

1. First pass scans your actual video to find the best 256 (or 128) colors
2. Second pass renders using those optimized colors

This gives you a smaller file that looks significantly better.

### Quick reference

```bash
# Simple (lower quality, bigger file)
ffmpeg -i input.mov -vf "fps=10,scale=600:-1" output.gif

# Good quality (palette optimization)
ffmpeg -i input.mov \
  -vf "fps=12,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  output.gif

# Best quality (full 256 colors, slower)
ffmpeg -i input.mov \
  -vf "fps=15,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=256:stats_mode=full[p];[s1][p]paletteuse=dither=floyd_steinberg" \
  output.gif
```

### Results for this project

| Metric | Before (.mov) | After (.gif) |
|--------|--------------|-------------|
| Size | 10 MB | 1.5 MB |
| Resolution | 1920x1080 | 800x450 |
| FPS | 100 | 12 |
| Duration | 55.8s | 55.8s |

---

*Add more learnings below as the project grows.*
