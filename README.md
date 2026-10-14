# cat-music-patterns

## Usage
- Used by `cmrt-client-playground`
  - Chord progressions
  - Tone.js timbres when in Tone.js mode (when `cmrt` is not running locally)
- Used by `cmrt`
  - `surge-xt-patch-voicing.json`: For chord/arpeggio detection on the keyboard screen (automatic detection results)
  - `surge-xt-patch-voicing-overrides.json`: Same as above (manual correction results)
- Used by `cat-plugin-player`
  - `surge-xt-patch-catalog.json`: A catalog for selecting Surge XT timbres in environments without `cmrt` (generated from Surge XT 1.3.4)
  - `surge-xt-fx-states.json`: Pre-prepared states for each Surge XT Effects preset. Indexed by SHA-256 of `.srgfx` (generated from Surge XT 1.3.4)

## Miscellaneous

### from-mutopia/
- Contains data freely available under the CC0 license, provided by The Mutopia Project.
  - For example, classical pieces like Bach's Toccata and Fugue in D minor, BWV 565.
  - The data is intended for use, for example, to perform part or all of Bach's Toccata and Fugue in D minor, BWV 565, either as-is or arranged.
  - The original data is placed as-is with the original URLs provided for user reference.
  - The benefits of CC0 include the ability to redistribute without permission, among others. We appreciate the efforts of The Mutopia Project staff.

## Frequent Breaking Changes