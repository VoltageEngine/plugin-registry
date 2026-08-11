#!/usr/bin/env python3
"""Point every listing at its plugin's latest GitHub release.

The catalogue used to be updated by the plugin repositories pushing to it, which needed a
cross-repository PAT on every plugin repo. No repo ever had one, so nothing was ever pushed and a
published release could sit for weeks while Browse Plugins offered the previous version. Reading is the
other direction and needs no secret at all: this repository's own GITHUB_TOKEN can query public releases
and write to this repository.

Curation still belongs to a human - which plugins are listed, and their Name/Description/Tags/Homepage,
are only ever changed by a pull request. This touches `Ref` and `Zip` and nothing else, and only ever
moves them forward, so a deleted or re-cut release can never roll a listing backwards.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

REGISTRY = "registry.json"
API = "https://api.github.com"

GITHUB_REPO = re.compile(r"github\.com[:/]+([^/]+)/(.+?)(?:\.git)?/?$")
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def parse_repo(entry):
    """owner/repo for a listing, or None when it is not hosted on GitHub."""
    for field in ("Git", "Homepage"):
        value = (entry.get(field) or "").strip()
        if not value:
            continue
        match = GITHUB_REPO.search(value)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def version_of(tag):
    """(major, minor, patch) for a tag, or None when it is not a version - a branch name, say."""
    match = SEMVER.match((tag or "").strip())
    return tuple(int(g) for g in match.groups()) if match else None


def latest_release(repo, token):
    """The repo's latest published release, or None when there is none or it cannot be read."""
    request = urllib.request.Request(
        f"{API}/repos/{repo}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "voltage-plugin-registry",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # 404 covers both "no releases yet" and a private repo this token cannot see. Neither is a
        # failure of the sync; the listing simply keeps whatever it already had.
        print(f"  {repo}: HTTP {error.code} - left unchanged")
        return None
    except Exception as error:  # noqa: BLE001 - a network blip must not fail the whole run
        print(f"  {repo}: {error} - left unchanged")
        return None


def zip_asset(release):
    """The release's package archive. `browser_download_url` is what the editor can actually fetch."""
    for asset in release.get("assets") or []:
        if (asset.get("name") or "").endswith(".zip"):
            return asset.get("browser_download_url")
    return None


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    data = json.loads(open(REGISTRY, encoding="utf-8").read())

    changes = []

    for entry in data.get("Plugins") or []:
        listing_id = entry.get("Id") or "(no id)"
        repo = parse_repo(entry)
        if not repo:
            print(f"{listing_id}: not a GitHub source - skipped")
            continue

        print(f"{listing_id}: checking {repo}")
        release = latest_release(repo, token)
        if not release:
            continue

        tag = (release.get("tag_name") or "").strip()
        archive = zip_asset(release)
        if not tag:
            continue

        if not archive:
            # A release whose CI never attached the package cannot be installed, so pointing the
            # catalogue at it would replace a working listing with a broken one.
            print(f"  {tag} has no .zip asset - left unchanged")
            continue

        current, latest = version_of(entry.get("Ref")), version_of(tag)

        if latest is None:
            print(f"  {tag} is not a version tag - left unchanged")
            continue

        if current is not None and latest <= current:
            print(f"  up to date at {entry.get('Ref')}")
            if entry.get("Zip") != archive and latest == current:
                entry["Zip"] = archive
                changes.append(f"{listing_id}: refreshed the {tag} archive URL")
            continue

        was = entry.get("Ref") or "(unset)"
        entry["Ref"] = tag
        entry["Zip"] = archive
        changes.append(f"{listing_id}: {was} -> {tag}")
        print(f"  {was} -> {tag}")

    if not changes:
        print("\nEverything already points at its latest release.")
        return 0

    with open(REGISTRY, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent="\t", ensure_ascii=False)
        handle.write("\n")

    summary = "\n".join(f"- {line}" for line in changes)
    print("\nUpdated:\n" + summary)

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write("### Registry updated\n\n" + summary + "\n")

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"changed=true\nsummary={'; '.join(changes)}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
