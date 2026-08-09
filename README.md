# Voltage Engine - Official Plugin Registry

The catalogue behind **Browse Plugins** in the Voltage editor. The editor reads
[`registry.json`](registry.json) straight from this repository's `main` branch:

```
https://raw.githubusercontent.com/VoltageEngine/plugin-registry/main/registry.json
```

Plugins are **not** bundled with the editor. They install per project, so a plugin fix ships on its own
schedule instead of waiting for an editor release.

## Adding your plugin

Open a pull request adding one entry to the `Plugins` array.

```json
{
	"Id": "yourname.yourplugin",
	"Name": "Your Plugin",
	"Description": "One sentence on what it does.",
	"Zip": "https://github.com/you/YourPlugin/releases/download/v1.0.0/yourname.yourplugin-1.0.0.zip",
	"Git": "https://github.com/you/YourPlugin.git",
	"Ref": "v1.0.0",
	"Author": "You",
	"Tags": ["gameplay"],
	"EngineVersion": ">=0.1.0",
	"Homepage": "https://github.com/you/YourPlugin"
}
```

| Field | Required | Notes |
|---|---|---|
| `Id` | yes | Globally unique, lowercase, dotted. Must match the `Id` in your `plugin.json`. |
| `Name` | yes | Display name. |
| `Description` | yes | One sentence - it is shown in the browser list. |
| `Zip` | preferred | Release archive. Pinned by content hash on install. |
| `Git` | optional | Clone URL. Only used when `Zip` is absent. |
| `Ref` | optional | Tag or branch for the `Git` source. |
| `Author` | no | |
| `Tags` | no | Free-form, used for filtering. |
| `EngineVersion` | no | Range such as `>=0.1.0`. Defaults to `*`. |
| `Homepage` | no | |

### Prefer `Zip` over `Git`

The Git resolver clones and reads `plugin.json` - it never builds. A Git source therefore has to commit
its built DLLs. A release archive lets your repository stay source-only and lets the editor pin the
download by content hash. Point `Zip` at a release asset and keep `lib/` and `editor-lib/` gitignored.

### Duplicate ids

The editor aggregates several registries and earlier entries win on a duplicate `Id`, so an entry here
cannot be shadowed by a registry added later.

## Running your own registry

The registry URL list in the editor is a list, not a single overridable link - an internal studio
catalogue sits alongside this one rather than replacing it. Host a `registry.json` in this same schema
and add its raw URL in the editor's plugin settings.
