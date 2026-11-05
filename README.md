# GearDrew website

The GearDrew studio website at https://geardrew.com: game portfolio, privacy policies and downloadable files.
Plain static HTML and CSS with no build step, hosted on GitHub Pages
(repo: https://github.com/drewripa/geardrew-website).

## Layout
- `index.html`: home page (games, about, contact)
- `games/<game>.html`: one page per game
- `privacy/<game>/index.html`: each game's own privacy policy, at `https://geardrew.com/privacy/<game>/`.
  Use that URL as the game's privacy policy in Google Play Console (and inside the game).
  `privacy.html` is the studio overview that links to them.
- `downloads.html`: press kit and other files. Put files in `files/` and add a line to the list.
  `files/google-play/` holds the Play developer page art (512 icon, 4096x2304 headers).
- `assets/`: CSS, the Geardrew Pixel font (Chunky style, from `D:\VibeGames\.tools\fonts`), logo, game art
- `404.html`: uses absolute paths from the domain root (`/`).
- `CNAME`: the custom domain, geardrew.com. `.nojekyll`: serve the files as they are.

## Tools (`pip install numpy pillow`)
- `tools/make_logo.py`: renders the voxel logo (`assets/img/logo.png`, `favicon.png`)
- `tools/logo_options.py OUT_DIR`: simplified logos for small sizes, with comparison sheets
- `tools/make_splash.py OUT.png`: the studio splash for the games' intros (logo with GearDrew to its right)
- `tools/make_play_assets.py TOWN.png`: Play developer page icon and headers (see the script for the town shot)

## Preview locally
`python -m http.server 8000` in this folder, then open http://localhost:8000.

## Publish
Pushing to `main` publishes the site (Settings > Pages > Source "Deploy from a branch", `main`, `/ (root)`).

Domain geardrew.com, at the domain registrar's DNS:
- `A` records for `@`: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- `AAAA` records for `@`: 2606:50c0:8000::153, 2606:50c0:8001::153, 2606:50c0:8002::153, 2606:50c0:8003::153
- `CNAME` record for `www`: drewripa.github.io

Then in Settings > Pages set the custom domain to geardrew.com and tick "Enforce HTTPS" once the
certificate is ready (Play requires https with a valid certificate for privacy policy links).

## Adding a game
1. Copy `games/silly-delivery.html` and add a card to the Games grid in `index.html`.
2. Copy a `privacy/<game>/` folder, change the name, and check every statement against what the game
   really does (permissions, network, SDKs, ads, purchases, what it saves). Link it from `privacy.html`,
   `downloads.html` and the game's page.
3. Add its press files to `downloads.html`.
