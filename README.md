# AJO Live

Live TV channel source (Stremio addon) for AJO TV.

- 2000+ live channels: Indian, news, sports, movies, kids, music
- Served as static JSON straight from this repo — no server to run
- Regenerated automatically every 6 hours from the AJO channel feed

## Install in AJO TV

Add-on URL:

```
https://raw.githubusercontent.com/imakshayjoshi/ajo-live/main/addon/manifest.json
```

Open AJO TV -> Settings -> Add-ons -> paste the URL -> Install. All channels appear
under the "AJO Live" catalog.

## How it works

- `generate_addon.py` builds the whole addon as static files:
  `manifest.json`, `catalog/`, `meta/`, `stream/`
- `.github/workflows/sync.yml` runs it on a schedule and commits any changes,
  so dead channels drop out and new channels appear automatically
- The upstream feed lives at new.ajo.co.in (channel list maintenance happens there)

## Regenerate manually

```
python3 generate_addon.py addon
```

## Channels by category

Category counts are in the repo; the full list with logos is in
`addon/catalog/channel/live.json` (paged 100 at a time).

## License

GPL-3.0. Channel stream data belongs to their respective owners. This repo only
publishes URLs already publicly listed in the AJO channel feed.
