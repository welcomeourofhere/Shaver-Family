# Shaver Family news feed

The existing daily VK job publishes `data/feed.json`. It now prepares WebP images
at 160, 320, 640, 960 and 1280 px, capped at the source width, with the original
aspect ratio. No resizing up, cropping or visual placeholders are introduced.

`media.variants` contains HTTPS URL, width, height and byte size. The compatible
`thumb_url` and `full_url` fields point to the generated files on this GitHub Pages
site. The main Shaver Family website consumes this array as `srcset`; older clients
can still display the feed via those two URLs. The original VK URLs are retained.

Media filenames contain an image-content hash. The daily workflow reuses files for
unchanged photos and commits the feed with its images in one commit. A wall API
failure leaves the previous published feed intact and fails the job. If one cover
cannot be prepared, that actual post and its original VK image/player are kept;
other images still receive WebP variants. No additional secrets are required.

Run `npm ci --ignore-scripts && npm test` before changing the pipeline. To optimise
an existing feed without a VK API call, run `npm run images`. To update posts and
images together, run the existing VK Feed Build workflow using its existing token.

The same daily task includes pinned posts (first, without duplicates) and video
posts. Video covers use the same WebP pipeline. Only a VK embed URL, video URL,
title and duration are exported; MP4 files are not downloaded or rehosted.
The website creates the VK iframe only after a visitor presses Play, and removes
it when the card closes or the feed page changes. If VK does not allow embedding,
the public video link remains available.

For public clips that omit a player in `video.get`, the job calls VK's open
`video.getOembed` method without a token. It extracts only an HTTPS VK iframe URL
for the requested owner/video ID; provider HTML is never included in the feed.
Clip posters from the exact `iv.okcdn.ru` host use the same bounded WebP pipeline.

Likes and views belong to the community post, including reposts. Missing counts
are null, not fabricated zero. Each item records stats_updated_at: this is a daily
snapshot, not live VK counters. Views are distinct from unique reach. The task
attempts stats.getPostReach with the existing token and exports only reach_total
when available; denied statistics access leaves reach null and does not stop news.
No token scopes, workflow schedule or secrets are changed.

The media ledger keeps the current and five previous successful feed versions.
Shared images are stored once. After a successful update, only obsolete files
owned by this pipeline are pruned. Failed whole-feed updates never run retention.
This does not remove anything in Yandex or the old website folder structure.
