#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plugin_id="io.github.thenailedone.codexusage"

if kpackagetool6 --type Plasma/Applet --list | grep -Fq "$plugin_id"; then
    kpackagetool6 --type Plasma/Applet --upgrade "$project_dir/package"
else
    kpackagetool6 --type Plasma/Applet --install "$project_dir/package"
fi

printf '%s\n' "Installed Codex Usage. Add it from Plasma's Add Widgets interface."
