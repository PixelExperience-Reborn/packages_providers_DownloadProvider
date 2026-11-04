#!/usr/bin/env python3
"""Check the historical PE DownloadProvider module/patch inventory only."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"


def ensure(ok: bool, label: str) -> None:
    if not ok:
        raise AssertionError(label)
    print("PASS INVENTORY:", label)


def read(path: str) -> str:
    p = ROOT / path
    ensure(p.is_file(), "legacy source file: " + path)
    return p.read_text(encoding="utf-8")


def main() -> None:
    bp = read("Android.bp")
    manifest = ET.parse(ROOT / "AndroidManifest.xml").getroot()
    constants = read("src/com/android/providers/downloads/Constants.java")
    receiver = read("src/com/android/providers/downloads/DownloadReceiver.java")
    notifier = read("src/com/android/providers/downloads/DownloadNotifier.java")
    thread = read("src/com/android/providers/downloads/DownloadThread.java")
    ui = read("ui/src/com/android/providers/downloads/ui/TrampolineActivity.java")

    ensure('name: "DownloadProvider"' in bp and 'certificate: "media"' in bp
           and "privileged: true" in bp, "old privileged media-signed provider")
    ensure('"com.android.providers.downloads.flags-aconfig-java"' not in bp,
           "old build lacks AOSP17 AConfig dependency")
    ensure(manifest.get("package") == "com.android.providers.downloads"
           and manifest.get(ANDROID + "sharedUserId") == "android.media",
           "shared media UID and APK package name")
    providers = {p.get(ANDROID + "authorities"): p
                 for p in manifest.findall("./application/provider")}
    ensure("downloads" in providers
           and "com.android.providers.downloads.documents" in providers,
           "legacy exported provider authorities")
    ensure(any(x.get(ANDROID + "pathPrefix") == "/all_downloads"
               and x.get(ANDROID + "permission") == "android.permission.ACCESS_ALL_DOWNLOADS"
               for x in providers["downloads"].findall("path-permission")),
           "legacy all_downloads path permission remains protected")
    for name in ("ACTION_PAUSE", "ACTION_RESUME", "ACTION_RESUME_QUEUE"):
        ensure(name in constants, "legacy custom receiver action " + name)
    ensure("manager.pauseDownload(id)" in receiver
           and "manager.resumeDownload(id)" in receiver,
           "old manual controls require framework DownloadManager APIs")
    ensure("STATUS_PAUSED_MANUAL" in thread
           and "STATUS_PAUSED_MANUAL" in notifier,
           "legacy manual pause status is threaded through provider and notifications")
    ensure("dm.pauseDownload(id)" in ui and "dm.resumeDownload(id)" in ui,
           "legacy UI calls manual pause and resume")
    ensure("text_download_speed" in notifier,
           "old optional speed-notification UI identified")

    print("PASS: historical code inventory only; AOSP17 compatibility and device tests NOT RUN.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ET.ParseError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
