# GearDrew site

The GearDrew studio website: game portfolio, privacy policy and downloadable files.
Plain static HTML and CSS with no build step, hosted on GitHub Pages.

## Layout
- `index.html`: home page (games, about, contact)
- `games/<game>.html`: one page per game
- `privacy.html`: privacy policy for all games, one section per game (`privacy.html#silly-delivery`).
  Use that URL as the privacy policy link in Google Play Console.
- `downloads.html`: press kit and other files. Put files in `files/` and add a line to the list.
- `assets/`: CSS, the Geardrew Pixel font (Chunky style, from `D:\VibeGames\.tools\fonts`), logo, game art
- `404.html`: uses absolute `/geardrew-site/` paths; change them if the repo is renamed or a custom domain is added.
- `.nojekyll`: serve the files as they are.

## Preview locally
`python -m http.server 8000` in this folder, then open http://localhost:8000.

## Publish
Push to GitHub, then in the repo: Settings > Pages > Source "Deploy from a branch", branch `main`, folder `/ (root)`.
The site appears at `https://<user>.github.io/geardrew-site/`.

## Adding a game
Copy `games/silly-delivery.html`, add a card to the Games grid in `index.html`, a section to `privacy.html`
and its press files to `downloads.html`.
