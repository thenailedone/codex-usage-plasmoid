# Codex Usage for KDE Plasma 6

An unofficial, native Plasma panel widget showing the remaining Codex usage in every window reported by Codex.

The compact panel display derives labels such as `5h` and `1w` from Codex's reported window lengths. It shows up to two windows plus a `+N` indicator; hover or click for every reported window, reset times, plan, additional-credit balance, reset credits, status, and the last update time.

This project is not affiliated with or endorsed by OpenAI or KDE.

## Features

- Native Plasma 6 compact and expanded representations
- Dynamic labels generated from Codex's reported window durations
- Handles one, two, or multiple quota buckets without assuming a fixed schedule
- Five-minute automatic refresh plus a manual refresh action
- ChatGPT sign-in through Codex's managed browser login
- Reuses an existing Codex login without copying or exposing credentials
- Clear states for missing Codex, signed-out accounts, and errors

## Requirements

- KDE Plasma 6
- Python 3
- A recent Codex CLI installation
- A ChatGPT account with Codex access

The initial release was tested on Plasma 6.6.6, Python 3.14, and Codex 0.155.0-alpha.9.2 on Ubuntu 26.04.

## Install a release

Download the `.plasmoid` file from the [latest release](https://github.com/thenailedone/codex-usage-plasmoid/releases/latest), then run:

```bash
kpackagetool6 --type Plasma/Applet --install codex-usage-*.plasmoid
```

Add **Codex Usage** from Plasma's **Add Widgets…** interface.

## Install from source

```bash
git clone https://github.com/thenailedone/codex-usage-plasmoid.git
cd codex-usage-plasmoid
./scripts/install.sh
```

## Authentication and privacy

The widget talks to the local `codex app-server`. Codex owns the ChatGPT login flow and credential storage; this widget never reads, copies, or stores access tokens. If you are signed out, the widget can ask Codex to open its managed ChatGPT browser login.

If Codex is installed in a non-standard location, set `CODEX_USAGE_CODEX_BIN` to its executable path in the Plasma environment.

API-key authentication is intentionally not treated as ChatGPT subscription usage because it has separate billing and limits.

## Build

```bash
./scripts/package.sh
```

The installable archive is written to `dist/`.

## Remove

```bash
kpackagetool6 --type Plasma/Applet --remove io.github.thenailedone.codexusage
```

## Limitations

The widget relies on Codex's app-server interface, which may evolve. Window durations and the number of quota buckets adapt automatically, but a future incompatible app-server change could still require a widget update. Browser cookies are never imported or inspected.

## License

MIT — see [LICENSE](LICENSE).
