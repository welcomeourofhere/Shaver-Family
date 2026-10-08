# Shaver Family news feed

The existing daily VK job publishes `data/feed.json`. It now prepares WebP images
at 160, 320, 640, 960 and 1280 px, capped at the source width, with the original
aspect ratio. No resizing up, cropping or visual placeholders are introduced.

`media.variants` contains HTTPS URL, width, height and byte size. The compatible
`thumb_url` and `full_url` fields point to the generated files on this GitHub Pages
site. The main Shaver Family website consumes this array as `srcset`; older clients
can still display the feed via those two URLs. The original VK URLs are retained.

Media filenames contain an image-content hash. The daily workflow reuses files for
unchanged photos and commits the feed with its images in one commit. A network,
API or encoder failure leaves the previous published feed intact and fails the
job, instead of publishing an empty feed. No additional secrets are required.

Run `npm ci --ignore-scripts && npm test` before changing the pipeline. To optimise
an existing feed without a VK API call, run `npm run images`. To update posts and
images together, run the existing VK Feed Build workflow using its existing token.
