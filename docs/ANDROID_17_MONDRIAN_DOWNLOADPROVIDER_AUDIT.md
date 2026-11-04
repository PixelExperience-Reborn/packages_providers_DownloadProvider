# P1 — DownloadProvider Android 17 / mondrian source and privilege audit

Date: 2026-11-04. **AUDIT ONLY — no Android17 source port, no manifest replacement, no runtime claims**.

## Version and source provenance

- Historical PixelExperience-Reborn source `packages_providers_DownloadProvider`, branch `seventeen`, HEAD `c9b69b9c349cb9361062d47bb7d3c744edfb2d7f` (merge of Android14 r22 on 2024-02-06). The name `seventeen` does **not** denote Android17 code.
- Official AOSP17 r1: `platform/packages/providers/DownloadProvider`, commit `20f95c184971841ba7c7fa9a74eeb0bb8cd5d8b2`, Git tree `8076bd37e0bb5a2fd62cff113e501075f21d68f4`. Provenance: https://android.googlesource.com/platform/packages/providers/DownloadProvider/+/refs/tags/android-17.0.0_r1
- The staged Android17 manifest already selects `platform/packages/providers/DownloadProvider` at `packages/providers/DownloadProvider`; the archived PE source is not selected.
- This is a **media-signed privileged provider** with `android.media` shared UID, exported `downloads` content-provider authority and `com.android.providers.downloads.documents` DocumentsProvider. A wholesale replacement can break URI grants, file ownership, scoped storage, background jobs, CTS and package signing.

## Verified architecture differences

- Legacy `Android.bp`: privileged `DownloadProvider`, media certificate, `platform_app_defaults`, `guava` only, Java source under `src`, `res`; no AConfig dependency.
- Official AOSP17 `Android.bp`: same privileged package and certificate, but adds `com.android.providers.downloads.flags-aconfig-java` and selects the correct stubs via `RELEASE_CONSCRYPT_NSC` (either `framework-conscrypt-nsc.stubs` or `framework-connectivity.stubs.module_lib`). Official blob SHA `5a96bb63e460bda203203f50670478a2001a0e62`; reference: https://android.googlesource.com/platform/packages/providers/DownloadProvider/+/refs/tags/android-17.0.0_r1/Android.bp
- Official AOSP17 manifest adds `RUN_USER_INITIATED_JOBS`, and its exported providers retain explicit per-path permissions. The implementation now integrates user-initiated jobs in download notifications; the old Android14 source cannot safely overwrite this behavior.
- Archive and current source include app/system-level download-provider permissions; keep the original `/my_downloads` UID restrictions and `/all_downloads` signature requirement; do not loosen URI permissions to make optional UI features work.

## Historical PE changes, split by functionality

| PE commit | Change | AOSP17 decision |
| --- | --- | --- |
| `bbe60db43f534f7c11bae3f0e78edbf6953a031b` (2016) | Manual pause/resume: modifies notification, receiver, thread, document provider, downloader UI; references `DownloadManager.pauseDownload()`, `resumeDownload()`, `PAUSED_MANUAL`, `Downloads.Impl.STATUS_PAUSED_MANUAL`, broadcast actions | **DEFER**: framework DownloadManager/Downloads and persisted state compatibility must be proven on API37, including job transitions, URI owners, notification intents and under/over-scoped privileges. It is NOT an isolated APK patch. |
| `d8a4513440d55db2583d1268e65eff15ea2bd672` (2014) | Download-speed and remaining-time text in notification with custom resources | **OPTIONAL CANDIDATE** only after current AOSP17 notification/UIJ logic, notification grouping, resources, overflow/speed-estimation and locale tests. Do not port old `DownloadNotifier.java` wholesale. |
| `8afc209bc76c69b5c284e2b9cb46d7a97c05e126` (2023) | Override newer `queryChildDocuments(..., includeHidden)` contract | **CHECK UPSTREAM** against current AOSP17 `DownloadStorageProvider`, otherwise copying it risks breaking document browsing and hidden-file policy. |

Official AOSP17 `Constants.java` currently lists `ACTION_OPEN/LIST/CANCEL/HIDE` but **not** legacy `ACTION_PAUSE/RESUME/RESUME_QUEUE`, and official `DownloadNotifier.java` includes `com.android.providers.downloads.flags.Flags` plus user-initiated job handling. This is a directly checked source-level difference, not a test of framework method availability: https://android.googlesource.com/platform/packages/providers/DownloadProvider/+/refs/tags/android-17.0.0_r1/src/com/android/providers/downloads/Constants.java

## Acceptance gates (required before replacing the system provider)

- [x] Confirm AOSP17 official source commit/tree, module metadata and exported provider contracts.
- [x] Identify archived PE pause/resume/speed patches and cross-module framework dependency risks.
- [x] Create standalone historical-source tests (not pretending to run Android17 code).
- [x] Prevent the archived PE provider from entering any AOSP17 staged manifest profile by accident.
- [ ] Audit the actual AOSP17 `DownloadManager.java`, `Downloads.java` internal status constants and caller/UID enforcement before considering manual pause/resume.
- [ ] Confirm stored download DB migrations, notification action authentication, broadcast receiver export rules, app UIDs, URI grants and multi-user/profile access.
- [ ] Verify `RELEASE_CONSCRYPT_NSC` and AConfig modules in a full AOSP17 source graph; build `m DownloadProvider` with current framework dependencies.
- [ ] Run `DownloadProviderTests`, `DownloadProviderPermissionTests`, `DownloadPublicApiAccessTests`, `CtsAppTestCases` DownloadManager and `CtsProviderTestCases` MediaStore tests.
- [ ] Test download lifecycle, cancel/retry/reboot, multi-user, scoped storage/SAF, UIJ foreground notifications and network loss on mondrian.
- [ ] Consider only small, separate, reviewed optional PE UI changes with host + Android + device regressions and no weakening of security.

## Decision

Retain official AOSP17 `packages/providers/DownloadProvider` unchanged. This audit changes no provider runtime code, database or system permission policy. No claim of successful AOSP17 Soong compilation, download tests or mondrian boot is made.
