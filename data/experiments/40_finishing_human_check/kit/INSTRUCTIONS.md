# Labelling instructions

Thank you for helping. You will look at satellite photos of 17 small city areas and say what changed between dates. The number of photos differs from area to area, so plan for several hours; you can stop and resume. You do not need to be a remote-sensing expert.

## What you get

- `images/` has these files for each area (S01 to S17):
  - `S01_d01.jpg`, `S01_d02.jpg`, `S01_d03.jpg`, and so on: the same place at several dates, at full detail. Image 1 (`d01`) is the oldest and the last image is the newest. The date is written on the top bar, together with the image number ("image 3 of 8"). Areas have different numbers of images, and the gaps between dates differ too (about half a year up to several years).
  - `S01_overview_a.jpg`, `S01_overview_b.jpg`, and so on: strips of up to four consecutive images side by side, smaller, numbered like the full images. Each strip repeats the last image of the previous one, so every pair of neighbouring images appears together in some strip. A thin bar on the first panel shows 100 m. Use a strip to get the big picture, then open the full images to check details.
- `labels_salma.csv`: your answer sheet. Open it in Excel.

## What to do

Each pair of consecutive images in an area is one decision (one interval). An area with 8 images has 7 intervals:

- Interval `1->2`: compare image 1 with image 2.
- Interval `2->3`: compare image 2 with image 3.
- and so on, up to the last pair.

The sheet has one row per interval, with the image numbers in the `interval` column. Label each interval on its own. Whatever happened in an earlier interval does not decide the next one: for `k->k+1`, compare image k only with image k+1. Some intervals are short and some are long; judge what you see between the two images.

For every row in the sheet, fill in `label` and `confidence`. The `note` column is optional (a few words are enough).

## The four labels

| Label | Meaning |
|---|---|
| `A` | New structure or vertical progress. New building frames, new floors, new footprints. |
| `B` | Finishing only. Buildings that already existed get facades, paint, windows, landscaping, paving or pools, with no new structure. |
| `C` | No visible change. |
| `U` | Cannot judge. Cloud, missing image, or too unclear. |

If you see both new structure and finishing in the same interval, choose `A`.

## Confidence

- `high`: you are sure.
- `low`: you are guessing or it is hard to see.

## Visual tips

- Shadows getting longer next to a building usually mean new floors were added (`A`).
- A crane, a bare concrete frame, or a fresh foundation means building work (`A`).
- A facade that changes colour, green lawns appearing, new dark paved roads, or blue swimming pools mean finishing (`B`), as long as the building itself is the same.
- Different sun angle or season can change shadows and colours by themselves. Only count changes that look real.
- If a part of the image is black or blank, that tile is missing. Judge only what you can see, and use `U` if too much is missing.

## Rules

- Do not look anything up (no maps, no search, no other photos).
- Do not discuss the images or your answers with anyone until you have finished all rows.
- Use only the images in this kit.

## Saving your work

Fill the three columns in `labels_salma.csv`: use capital letters `A`, `B`, `C` or `U` in `label`, and `high` or `low` in `confidence`. Save as CSV (keep the file name) and send it back when all rows are done.

## Labelling in the browser (alternative to Excel)

1. Put the `images/` folder in this `kit/` folder, then run `python make_manifest.py` (no installs). It writes `manifest.js`.
2. Double-click `label.html` to open it in a browser (no server needed). It shows one interval at a time with two images side by side; click an image to enlarge it.
3. Press `a`/`b`/`c`/`u` for the label, `h`/`l` for high/low confidence, and the left/right arrows to move. Answers are saved in the browser as you go; you can close the page and resume later on the same computer and browser.
4. When done, click **Export CSV**. It downloads `labels_salma.csv` (columns `id,interval,label,confidence,note`, same as the Excel sheet); send that file back. The Excel route above still works.

## Rights

The images come from Esri Wayback and are for this internal labelling only. Do not share them, post them, or upload them anywhere.
