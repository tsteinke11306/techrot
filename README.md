# TechRot

> AI model comparisons & AI news — YouTube channel assets and website.

## Contents

| File | Description |
|------|-------------|
| `techrot-banner.html` | YouTube banner source (2560×1440, ASCII style, monochrome) |
| `techrot-banner.png` | Exported YouTube banner image |
| `index.html` | Website draft — landing page for the TechRot channel |
| `profile-pic.html` | Profile picture source (512×512, ASCII fractured skull) |
| `profile-pic.png` | Exported profile picture image |

## Design

All assets share a monochrome ASCII aesthetic:
- **Colors:** greys, whites, blacks only — no color accents
- **Typography:** JetBrains Mono / Consolas (monospace)
- **Texture:** subtle scanlines + grid overlay for a CRT/terminal feel
- **Title:** ANSI Shadow figlet font with fracture-style color split

## Exporting Images

Banner and profile picture HTML files can be exported to PNG using headless Chrome/Edge:

```bash
# YouTube banner (2560×1440)
msedge --headless --disable-gpu --screenshot="techrot-banner.png" --window-size=2560,1440 "file:///path/to/techrot-banner.html"

# Profile picture (512×512)
msedge --headless --disable-gpu --screenshot="profile-pic.png" --window-size=512,512 "file:///path/to/profile-pic.html"
```