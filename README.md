# Psy Trance Rolling Basslines

Original note-only MIDI studies of rolling monophonic basslines. Eight studies, two bass variations each. Harmonic references and kicks are cataloged separately and are not part of the core count.

GitHub repository: https://github.com/mizcausevic-dev/psy-trance-rolling-basslines. This repository is private. The MIDI files, preview audio, film, stills, and catalog page are produced in this repository from the generator.

## What you can open

- `index.html` is the file catalog.
- `midi/arrangement.mid` is a Format 1 preview arrangement of study 01, variation A, its harmonic reference, and kick-a.
- Individual Format 0 parts live under `midi/`.
- `midi/validation-Cursor.json` is the report from reopening those exact bytes.
- `preview/preview.mp3` is the primary music preview. It is 27.455 seconds in the encoded file. preview, not a master.
- `film/preview.mp4` and `film/preview.vtt` are the film. On-picture and caption text is `preview, not master`.
- `art/hero.jpg` is a 1280x720 illustration. `art/square.jpg` is 1080x1080. Neither is a photograph.

Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.

## Studies

- s01 Downbeat Void: 140 BPM, 16 bars, A Phrygian, tonic reference A.
- s02 Offbeat Ladder: 144 BPM, 8 bars, E Phrygian dominant, tonic reference E.
- s03 Fifth Gate: 138 BPM, 16 bars, D harmonic minor, tonic reference D.
- s04 Short Gate Engine: 146 BPM, 8 bars, F# Phrygian, tonic reference F#.
- s05 Held Fifth: 142 BPM, 16 bars, G Phrygian, tonic reference G.
- s06 Five-Cell Crawl: 148 BPM, 8 bars, pitch-class set {0, 1, 3, 6, 7}, tonic reference no fixed tonic.
- s07 Question and Gap: 141 BPM, 16 bars, C Hungarian minor, tonic reference C.
- s08 Displaced Octave: 145 BPM, 8 bars, Bb natural minor, tonic reference Bb.

Core bass files: 16. Reference files: 19.

Pitched notes are MIDI 28 through 60. C4 is 60. PPQ is 960. Meter is 4/4. Bass is monophonic. Offsets are 0. Seeds identify studies and are not random draws. Generator 1.0.0.

## Preview path

The preview renders the canonical notes for `s01.bass.a`, `s01.harmonic`, and `s01.kick.a` with `simple-synth-1.0.0`. Tempo authority is the encoded microsecond value in the MIDI, 428571 us per quarter note. Sample positions use `floor(seconds * 44100 + 0.5)` from tick 0. Intervals are not summed. Sample-exact repeating loops at an arbitrary BPM are not promised.

The synth mapping is a saw bass, a triangle harmonic layer, and a sine-sweep kick. No program changes are encoded. A conventional GM player will normally use its default piano program for pitched channels unless configured otherwise; compatible GM channel 10 percussion is treated separately. Player behavior may vary. The mapping is not encoded in the MIDI.

Encoded MP3 settings: libmp3lame, 192 kbps. Film audio is AAC at 160 kbps re-encoded from that MP3, so the decoded film audio is not byte-identical to the MP3. Film duration probe: 27.428 seconds. MP3 container probe 27.455 seconds. MP4 probe 27.428 seconds. The film ends on a video frame, so it is slightly shorter than the MP3 container. The music is the same preview, not a different excerpt. The picture is a still illustration with rasterized disclosure text. DejaVu Sans Bold from the build machine supplies the glyphs. The font file is not in this pack.

No human listening audition was performed for this build. A sample peak is recorded in the preview manifest. It is not LUFS and it is not a true peak.

## Build

From the repository root, with Python 3.11+ and ffmpeg (libmp3lame, aac, libx264):

```bash
python3 tools/build_pack.py
python3 -m http.server 41773
```

The page is static. It is served with Python's HTTP server so the MIDI and media keep working relative paths. There is no application server and no package install. Standard library only.

`build/` holds the intermediate WAV, the procedural PPM, and the film plate. Those files are gitignored. The delivered audio is the MP3.

## Checks the validator actually runs

File existence, parse, PPQ, tempo, 4/4, end-of-track boundary, note pairing, ranges, monophonic bass, harmonic polyphony cap, channel 10 note 36 only, note-off before note-on at a shared tick, absence of program changes and other channel messages, agreement with the canonical score, and agreement between `arrangement.mid` and the three source files. A negative overlap fixture is written outside the pack and must be rejected.

## Drafts and publication

Social captions, the X post, and the Medium article are drafts. They are not access controls. If this repository is public, the drafts are public. Do not treat them as posted to Instagram, X, or Medium.

Repository description: Original note-only MIDI studies of rolling monophonic psytrance basslines, with matched validation and a simple-synth preview.

Topics: midi, psytrance, bassline, music-production, electronic-music, composition, general-midi, study-pack.

No release tag was created. No public live page URL has been verified. `index.html` keeps its name because players and links depend on it.

## Limitations

Variation compatibility is per study and is written on the page. Do not assume one kick fits both bass variations. The arrangement is only study 01. Stacking it with the part files doubles those notes.
