# cat-music-patterns

## Usage
- Used by cmrt-client-playground
  - Chord progressions
  - Tone.js timbres when in Tone.js mode (when cmrt is not running locally)
- Used by cmrt
  - `surge-xt-patch-voicing.json` : For identifying chords/arpeggios on the keyboard screen (automatic detection results)
  - `surge-xt-patch-voicing-overrides.json` : Same as above (manual correction results)
- Used by cat-plugin-player
  - `surge-xt-patch-catalog.json` : For enabling timbre selection in environments without cmrt
  - `surge-xt-fx-states.json` : For playing Effects presets quickly
  - `surge-xt-start-delay.json` : For determining if a timbre can be played without a delay
  - `patch-pitch-tracking.json` : For determining if timbres in the drum/percussion section should be moved to the pitched percussion section

## Miscellaneous

### from-mutopia/
- Contains data freely usable under the CC0 license, provided by The Mutopia Project.
  - For example, classical music, Bach's Toccata and Fugue in D minor, BWV 565.
  - The data is intended for purposes such as playing part or all of Bach's Toccata and Fugue in D minor, BWV 565, either as-is or arranged.
  - The original data is placed as-is, with its original URL provided for user reference.
  - Benefits of CC0 include enabling redistribution without permission, among others. We thank The Mutopia Project staff for their efforts.

## Frequent Breaking Changes