"""Original compositions for Psy Trance Rolling Basslines.

Container lengths, tempos, tonics, and pitch collections are fixed in STUDIES
before any note is written. Seeds identify studies. No stochastic draws are used.
Offsets are 0, so performed_start equals nominal_start.

Pitched notes stay in MIDI 28-60. Bass parts are monophonic. Channel 10 kick
references use GM acoustic bass drum (note 36) only.
"""

from __future__ import annotations

from tools.midi_io import BAR_TICKS_4_4, PPQ, bpm_to_us, effective_bpm

GENERATOR_VERSION = "1.0.0"
PACK_ID = "psy-trance-rolling-basslines"
PACK_NAME = "Psy Trance Rolling Basslines"
PITCH_LO = 28
PITCH_HI = 60

# Degree tables. Index 0 is the lowest listed chord tone, not always the tonic octave.
S01 = [33, 34, 36, 38, 40, 41, 43, 45, 46, 48, 50, 52, 53, 55]
S02 = [28, 29, 32, 33, 35, 36, 38, 40, 41, 44, 45, 47, 48, 50, 52, 53]
S03 = [38, 40, 41, 43, 45, 46, 49, 50, 52, 53, 55, 57, 58]
S04 = [30, 31, 33, 35, 37, 38, 40, 42, 43, 45, 47, 49, 50, 52, 54]
S05 = [31, 32, 34, 36, 38, 39, 41, 43, 44, 46, 48, 50, 51, 53, 55]
S07 = [36, 37, 40, 41, 43, 44, 47, 48, 49, 52, 53, 55, 56, 59, 60]
S08 = [34, 36, 37, 39, 41, 42, 44, 46, 48, 49, 51, 53, 54, 56, 58]

S01A = [
    ".001.001.001.001",
    ".010.010.010.010",
    ".002.001.002.001",
    ".012.010.021.001",
    ".040.201.040.210",
    ".402.140.024.401",
    ".240.420.104.042",
    ".401.042.014.401",
    ".789.798.789.879",
    ".897.978.879.789",
    ".978.897.789.978",
    ".b9a.a98.987.879",
    "..7...6...5...4.",
    "..3...2...1...0.",
    "......7.......0.",
    "......0.......0.",
]

S02A = [
    ".0.1.2.3.4.5.6.7",
    ".7.6.5.4.3.2.1.0",
    ".0.2.3.5.7.5.3.2",
    "........7.6.5.4.",
    ".7.8.9.a.b.c.d.e",
    ".e.c.b.9.7.5.3.0",
    ".4.5.4.5.4.5.4.5",
    ".7..............",
]

S02B = [
    "..7...6...5...4.",
    "..4...3...2...1.",
    "..2...2...5...5.",
    "..4...5...4...5.",
    "..a...9...8...7.",
    "..7...5...4...0.",
    "................",
    "..0...........0.",
]


class Part:
    def __init__(
        self,
        study: dict,
        part_id: str,
        role: str,
        variation: str | None,
        core: bool,
        channel: int,
        file_slug: str,
        monophonic: bool,
        max_poly: int,
        collection: set[int] | None,
        pitch_lo: int = PITCH_LO,
        pitch_hi: int = PITCH_HI,
    ) -> None:
        self.study = study
        self.part_id = part_id
        self.role = role
        self.variation = variation
        self.core = core
        self.channel = channel
        self.file_slug = file_slug
        self.monophonic = monophonic
        self.max_poly = max_poly
        self.collection = collection
        self.pitch_lo = pitch_lo
        self.pitch_hi = pitch_hi
        self.container_ticks = study["bars"] * BAR_TICKS_4_4
        self.notes: list[dict] = []

    def add(self, start: int, duration: int, pitch: int, velocity: int, departure: bool = False) -> None:
        if not isinstance(start, int) or not isinstance(duration, int):
            raise TypeError("start and duration must be integers")
        end = start + duration
        if start < 0 or duration <= 0 or start >= self.container_ticks or end > self.container_ticks:
            raise ValueError(f"{self.part_id} boundary {start}+{duration} container {self.container_ticks}")
        if not self.pitch_lo <= pitch <= self.pitch_hi:
            raise ValueError(f"{self.part_id} pitch {pitch} outside {self.pitch_lo}-{self.pitch_hi}")
        if not 1 <= velocity <= 127:
            raise ValueError(velocity)
        if self.collection is not None and pitch not in self.collection and not departure:
            raise ValueError(f"{self.part_id} pitch {pitch} is outside the collection and is not a departure")
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            overlaps = start < o1 and o0 < end
            if not overlaps:
                continue
            if self.monophonic or other["pitch"] == pitch:
                raise ValueError(
                    f"{self.part_id} overlap {other['pitch']}@{o0} with {pitch}@{start}"
                )
        active = 1
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            if start < o1 and o0 < end:
                active += 1
        if active > self.max_poly:
            raise ValueError(f"{self.part_id} polyphony {active}")
        self.notes.append({
            "nominal_start": start,
            "offset": 0,
            "performed_start": start,
            "duration": duration,
            "pitch": pitch,
            "velocity": velocity,
            "channel": self.channel,
            "departure": departure,
        })

    def finish(self) -> dict:
        ordered = sorted(self.notes, key=lambda n: (n["performed_start"], n["pitch"], n["duration"]))
        for index, note in enumerate(ordered, start=1):
            note["id"] = f"{self.part_id}.n{index:04d}"
            if note["performed_start"] != note["nominal_start"] + note["offset"]:
                raise ValueError("offset identity failed")
        if self.core and len(ordered) < 8:
            raise ValueError(f"{self.part_id} has too few notes to be a core part")
        if len(ordered) < 1:
            raise ValueError(f"{self.part_id} is empty")
        return {
            "id": self.part_id,
            "study_id": self.study["id"],
            "slug": self.study["slug"],
            "role": self.role,
            "variation": self.variation,
            "core": self.core,
            "channel": self.channel,
            "file_slug": self.file_slug,
            "path": f"midi/{self.study['slug']}/{self.file_slug}.mid",
            "monophonic": self.monophonic,
            "max_poly": self.max_poly,
            "container_ticks": self.container_ticks,
            "container_bars": self.study["bars"],
            "bpm": self.study["bpm"],
            "tempo_us": self.study["tempo_us"],
            "notes": ordered,
        }


def _gate_ok(gate: int, gap: int, label: str) -> int:
    if gate > gap or gate <= 0:
        raise ValueError(f"{label} gate {gate} gap {gap}")
    return gate


def from_patterns(part: Part, patterns: list[str], scale: list[int], gate_for_bar, velocity_for, departures=None) -> None:
    departures = departures or {}
    if len(patterns) != part.study["bars"]:
        raise ValueError(f"{part.part_id} expected {part.study['bars']} bars, got {len(patterns)}")
    pending = []
    for bar, pattern in enumerate(patterns):
        if len(pattern) != 16:
            raise ValueError(f"{part.part_id} bar {bar} length {len(pattern)}: {pattern}")
        for step, char in enumerate(pattern):
            if char == ".":
                continue
            key = (bar, step)
            if key in departures:
                pitch = departures[key]
                departure = True
            else:
                degree = int(char, 16)
                if degree >= len(scale):
                    raise ValueError(f"{part.part_id} degree {degree} bar {bar}")
                pitch = scale[degree]
                departure = False
            pending.append((bar, step, pitch, departure))
    for index, (bar, step, pitch, departure) in enumerate(pending):
        start = bar * BAR_TICKS_4_4 + step * (PPQ // 4)
        if index + 1 < len(pending):
            nbar, nstep, _, _ = pending[index + 1]
            gap = nbar * BAR_TICKS_4_4 + nstep * (PPQ // 4) - start
        else:
            gap = part.container_ticks - start
        gate = gate_for_bar(bar) if callable(gate_for_bar) else gate_for_bar
        duration = _gate_ok(gate, gap, f"{part.part_id} bar {bar} step {step}")
        part.add(start, duration, pitch, velocity_for(bar, step), departure=departure)


def add_items(part: Part, items: list[tuple]) -> None:
    """items are (start, duration, pitch, velocity, departure)."""
    ordered = sorted(items, key=lambda item: (item[0], item[2]))
    for index, (start, duration, pitch, velocity, departure) in enumerate(ordered):
        if index + 1 < len(ordered):
            gap = ordered[index + 1][0] - start
            if gap <= 0 and part.monophonic:
                raise ValueError(f"{part.part_id} unsorted or stacked start {start}")
        part.add(start, duration, pitch, velocity, departure=departure)


def _hold(scale, degree, bar, bars, velocity):
    return (bar * BAR_TICKS_4_4, bars * BAR_TICKS_4_4, scale[degree], velocity, False)


def _step(bar, step):
    return bar * BAR_TICKS_4_4 + step * (PPQ // 4)


def studies() -> list[dict]:
    rows = [
        {
            "id": "s01",
            "slug": "s01-downbeat-void",
            "title": "Downbeat Void",
            "bpm": 140,
            "bars": 16,
            "tonic": "A",
            "tonal_reference": "A",
            "collection_name": "A Phrygian",
            "pitch_classes": [9, 10, 0, 2, 4, 5, 7],
            "departures": [],
            "seed": 14001,
            "identity": "Sixteenth-note rolls leave every quarter-note downbeat empty, accent the offbeat, then thin into long gates on the &.",
            "limitations": "Variation B puts attacks on the downbeat and leaves the & empty. Use kick-b with variation B. Kick-a fits variation A.",
        },
        {
            "id": "s02",
            "slug": "s02-offbeat-ladder",
            "title": "Offbeat Ladder",
            "bpm": 144,
            "bars": 8,
            "tonic": "E",
            "tonal_reference": "E",
            "collection_name": "E Phrygian dominant",
            "pitch_classes": [4, 5, 8, 9, 11, 0, 2],
            "departures": [],
            "seed": 14402,
            "identity": "Odd sixteenths climb and fall through the mode. Bar 4 is half silent. Variation B moves the same color onto the & and rests for a full bar.",
            "limitations": "Variation A bar 4 also sounds on beat 3's downbeat, so a quarter-note kick shares that tick on another channel. The kick reference is one quarter-note pattern for both variations.",
        },
        {
            "id": "s03",
            "slug": "s03-fifth-gate",
            "title": "Fifth Gate",
            "bpm": 138,
            "bars": 16,
            "tonic": "D",
            "tonal_reference": "D",
            "collection_name": "D harmonic minor",
            "pitch_classes": [2, 4, 5, 7, 9, 10, 1],
            "departures": ["Variation A bar 13 substitutes C3 (48) for a collection tone.", "Variation B bar 16 substitutes Eb3 (51)."],
            "seed": 13803,
            "identity": "Root and fifth alternate on a 3+3+2 sixteenth grid with the bar downbeat left open. Variation B flips the grid to 3+2+3 and treats the fifth as the pedal.",
            "limitations": "Lowest written D in range is D2 (38). D1 is outside the pack range and is not used. One kick marks only the bar downbeat.",
        },
        {
            "id": "s04",
            "slug": "s04-short-gate-engine",
            "title": "Short Gate Engine",
            "bpm": 146,
            "bars": 8,
            "tonic": "F#",
            "tonal_reference": "F#",
            "collection_name": "F# Phrygian",
            "pitch_classes": [6, 7, 9, 11, 1, 2, 4],
            "departures": [],
            "seed": 14604,
            "identity": "Variation A is a low, mostly stepwise engine with 70-tick gates and a rest on the downbeat of every other bar. Variation B is a five-note loop an octave up, with a whole beat removed every third beat.",
            "limitations": "Kick-a only marks variation A's even-bar downbeats. It does not clear every remaining bass attack. Kick-b marks the beats variation B leaves empty.",
        },
        {
            "id": "s05",
            "slug": "s05-held-fifth",
            "title": "Held Fifth",
            "bpm": 142,
            "bars": 16,
            "tonic": "G",
            "tonal_reference": "G",
            "collection_name": "G Phrygian",
            "pitch_classes": [7, 8, 10, 0, 2, 3, 5],
            "departures": [],
            "seed": 14205,
            "identity": "Multi-bar G and D holds are cut by single-bar bursts. Variation B moves the holds to Ab and Eb and breaks the bursts into fewer attacks.",
            "limitations": "The half-time kick shares time with held bass notes on a different channel. It is a marker, not a mute of the hold.",
        },
        {
            "id": "s06",
            "slug": "s06-five-cell-crawl",
            "title": "Five-Cell Crawl",
            "bpm": 148,
            "bars": 8,
            "tonic": None,
            "tonal_reference": "no fixed tonic",
            "collection_name": "pitch-class set {0, 1, 3, 6, 7}",
            "pitch_classes": [0, 1, 3, 6, 7],
            "departures": ["Variation A bar 7 step 5 substitutes F2 (41).", "Variation B bar 4 step 5 substitutes G#2 (44)."],
            "seed": 14806,
            "identity": "A five-pitch cell rotates once per bar on a grid that leaves two downbeats empty. Variation B uses a retrograde rotation, the opposite rest grid, and a different departure pitch.",
            "limitations": "Kick-a fits variation A. Kick-b fits variation B. Do not treat either kick as compatible with the other bass variation.",
        },
        {
            "id": "s07",
            "slug": "s07-question-and-gap",
            "title": "Question and Gap",
            "bpm": 141,
            "bars": 16,
            "tonic": "C",
            "tonal_reference": "C",
            "collection_name": "C Hungarian minor",
            "pitch_classes": [0, 1, 4, 5, 7, 8, 11],
            "departures": [],
            "seed": 14107,
            "identity": "Each four-bar cycle asks a denser question, then leaves a long gap with one held C. Variation B replaces the gap with a descending answer on eighth notes.",
            "limitations": "The kick reference is carved to variation A's gaps. Variation B does not keep those gaps.",
        },
        {
            "id": "s08",
            "slug": "s08-displaced-octave",
            "title": "Displaced Octave",
            "bpm": 145,
            "bars": 8,
            "tonic": "Bb",
            "tonal_reference": "Bb",
            "collection_name": "Bb natural minor",
            "pitch_classes": [10, 0, 1, 3, 5, 6, 8],
            "departures": ["Variation A uses A1 (33) as a lower neighbor.", "Variation B uses B2 (47) in place of F."],
            "seed": 14508,
            "identity": "Syncopated octave leaps sit inside beats 2 and 4. Variation B shifts the grid later by one eighth, swaps octaves for fifths, and inverts which note of the leap is loud.",
            "limitations": "One kick on beats 1 and 3, duration 90 ticks, fits both variations because those bass attacks start after the kick has ended. Variation B does sound inside beats 1 and 3, just not on the tick the kick uses.",
        },
    ]
    for row in rows:
        if not 138 <= row["bpm"] <= 148:
            raise ValueError(row["bpm"])
        row["tempo_us"] = bpm_to_us(row["bpm"])
        row["effective_bpm"] = effective_bpm(row["tempo_us"])
        row["meter"] = "4/4"
        row["bar_ticks"] = BAR_TICKS_4_4
        row["ppq"] = PPQ
        row["stochastic_draws"] = 0
    return rows


def _collection(scale: list[int]) -> set[int]:
    return set(scale)


def _bass(study, variation, slug="bassline"):
    return Part(
        study,
        f"{study['id']}.bass.{variation}",
        "bassline",
        variation,
        True,
        0,
        f"{slug}-{variation}",
        True,
        1,
        None,
    )


def _harm(study, collection):
    return Part(
        study,
        f"{study['id']}.harmonic",
        "harmonic-reference",
        None,
        False,
        1,
        "harmonic-reference",
        False,
        2,
        collection,
    )


def _kick(study, variation, slug):
    return Part(
        study,
        f"{study['id']}.kick.{variation}",
        "kick-reference",
        variation,
        False,
        9,
        slug,
        True,
        1,
        {36},
        36,
        36,
    )


def _s01(study: dict) -> list[Part]:
    bass_a = _bass(study, "a")
    from_patterns(
        bass_a,
        S01A,
        S01,
        lambda bar: 150 if bar < 8 else 170 if bar < 12 else 400,
        lambda bar, step: 114 if step in (2, 6, 10, 14) else 86,
    )
    bass_b = _bass(study, "b")
    motif_sets = {
        "early": ([0, 2, 1, 4, 3], [0, 1, 3, 4, 5, 7, 8, 9, 11, 12, 13, 15], range(0, 8), 150),
        "mid": ([4, 6, 5, 1, 0], [1, 3, 5, 7, 9, 11, 13, 15], range(8, 12), 80),
        "late": ([7, 9, 8, 11, 10], [1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15], range(13, 16), 120),
    }
    pending = []
    for degrees, slots, bars, gate in motif_sets.values():
        cursor = 0
        for bar in bars:
            for step in slots:
                pending.append((bar, step, S01[degrees[cursor % len(degrees)]], gate))
                cursor += 1
    pending.sort()
    for index, (bar, step, pitch, gate) in enumerate(pending):
        start = _step(bar, step)
        gap = (pending[index + 1][0] * BAR_TICKS_4_4 + pending[index + 1][1] * 240 - start) if index + 1 < len(pending) else bass_b.container_ticks - start
        if bar < 8:
            velocity = 112 if step in (0, 4, 8, 12) else 78
        elif bar < 12:
            velocity = 70
        else:
            velocity = 108 if step in (2, 6, 10, 14) else 84
        bass_b.add(start, _gate_ok(gate, gap, "s01b"), pitch, velocity)
    harm = _harm(study, _collection(S01))
    add_items(harm, [
        (_step(0, 0), 2 * BAR_TICKS_4_4, S01[0], 54, False),
        (_step(0, 0), 2 * BAR_TICKS_4_4, S01[4], 48, False),
        (_step(4, 0), 3 * BAR_TICKS_4_4, S01[1], 52, False),
        (_step(4, 0), 3 * BAR_TICKS_4_4, S01[5], 46, False),
        (_step(8, 0), 3 * BAR_TICKS_4_4, S01[7], 56, False),
        (_step(8, 0), 3 * BAR_TICKS_4_4, S01[11], 50, False),
        (_step(12, 0), 2 * BAR_TICKS_4_4, S01[0], 50, False),
        (_step(12, 0), 2 * BAR_TICKS_4_4, S01[4], 44, False),
    ])
    kick_a = _kick(study, "a", "kick-a")
    kick_b = _kick(study, "b", "kick-b")
    for bar in range(16):
        for beat in range(4):
            kick_a.add(_step(bar, beat * 4), 100, 36, 116 if beat == 0 else 98)
            kick_b.add(_step(bar, beat * 4 + 2), 80, 36, 104)
    return [bass_a, bass_b, harm, kick_a, kick_b]


def _s02(study: dict) -> list[Part]:
    bass_a = _bass(study, "a")
    from_patterns(
        bass_a,
        S02A,
        S02,
        lambda bar: 1440 if bar == 7 else 200,
        lambda bar, step: 110 if step in (1, 5, 9, 13) else 82,
    )
    bass_b = _bass(study, "b")
    from_patterns(
        bass_b,
        S02B,
        S02,
        lambda bar: 400,
        lambda bar, step: 72 if bar < 4 else 110,
    )
    harm = _harm(study, _collection(S02))
    add_items(harm, [
        (_step(0, 0), 2 * BAR_TICKS_4_4, S02[0], 50, False),
        (_step(0, 0), 2 * BAR_TICKS_4_4, S02[4], 44, False),
        (_step(3, 0), 2 * BAR_TICKS_4_4, S02[3], 52, False),
        (_step(3, 0), 2 * BAR_TICKS_4_4, S02[7], 46, False),
        (_step(6, 0), BAR_TICKS_4_4, S02[4], 48, False),
        (_step(6, 0), BAR_TICKS_4_4, S02[8], 42, False),
    ])
    kick = _kick(study, "a", "kick-reference")
    for bar in range(8):
        for beat in range(4):
            kick.add(_step(bar, beat * 4), 100, 36, 114 if beat == 0 else 96)
    return [bass_a, bass_b, harm, kick]


def _s03(study: dict) -> list[Part]:
    steps_a = [3, 6, 8, 11, 14]
    rows_a = [
        [0, 4, 0, 4, 0],
        [4, 0, 4, 0, 4],
        [0, 4, 0, 4, 0],
        [4, 0, 4, 2, 0],
        [0, 4, 2, 6, 0],
        [0, 6, 4, 2, 0],
        [2, 0, 6, 4, 0],
        [0, 4, 6, 4, 0],
        [7, 11, 7, 11, 7],
        [11, 7, 11, 7, 11],
        [7, 11, 9, 6, 7],
        [7, 11, 7, 12, 7],
        [0, 4, 0, 4, 0],
        [0, 4, 0, 4, 0],
        [7, 4, 0, 4, 7],
        [0, 4, 0, 4, 0],
    ]
    bass_a = _bass(study, "a")
    items = []
    for bar, row in enumerate(rows_a):
        for step, degree in zip(steps_a, row):
            departure = bar == 12 and step == 14
            pitch = 48 if departure else S03[degree]
            rootish = pitch in (S03[0], S03[7])
            gate = 180 if departure or not rootish else 400
            velocity = 96 if departure else 108 if rootish else 76
            items.append((_step(bar, step), gate, pitch, velocity, departure))
    add_items(bass_a, items)

    steps_b = [3, 5, 8, 11, 13]
    rows_b = [
        [4, 0, 4, 4, 0],
        [4, 0, 4, 4, 0],
        [4, 2, 4, 0, 4],
        [4, 0, 4, 2, 4],
        [4, 2, 4, 6, 4],
        [4, 6, 4, 2, 4],
        [11, 7, 11, 6, 11],
        [11, 7, 11, 7, 11],
        [11, 7, 11, 11, 7],
        [11, 9, 11, 7, 11],
        [11, 7, 11, 12, 11],
        [11, 7, 11, 7, 11],
        [4, 0, 4, 0, 4],
        [4, 2, 4, 0, 4],
        [4, 0, 4, 0, 4],
        [4, 0, 4, 0, 4],
    ]
    bass_b = _bass(study, "b")
    items = []
    for bar, row in enumerate(rows_b):
        for index, (step, degree) in enumerate(zip(steps_b, row)):
            departure = bar == 15 and index == 3
            pitch = 51 if departure else S03[degree]
            fifth = pitch in (S03[4], S03[11])
            velocity = 90 if departure else 112 if fifth else 70
            items.append((_step(bar, step), 180 if departure else 200, pitch, velocity, departure))
    add_items(bass_b, items)

    harm = _harm(study, _collection(S03))
    add_items(harm, [
        (_step(0, 0), 3 * BAR_TICKS_4_4, S03[0], 50, False),
        (_step(0, 0), 3 * BAR_TICKS_4_4, S03[4], 44, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S03[0], 48, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S03[6], 42, False),
        (_step(8, 0), 3 * BAR_TICKS_4_4, S03[7], 52, False),
        (_step(8, 0), 3 * BAR_TICKS_4_4, S03[11], 46, False),
        (_step(12, 0), 2 * BAR_TICKS_4_4, S03[0], 46, False),
        (_step(12, 0), 2 * BAR_TICKS_4_4, S03[2], 40, False),
    ])
    kick = _kick(study, "a", "kick-reference")
    for bar in range(16):
        kick.add(_step(bar, 0), 140, 36, 118)
    return [bass_a, bass_b, harm, kick]


def _s04(study: dict) -> list[Part]:
    bass_a = _bass(study, "a")
    sounding = []
    sounding_index = 0
    for bar in range(8):
        for step in range(16):
            if bar % 2 == 0 and step == 0:
                continue
            if bar == 7 and step >= 12:
                continue
            if bar < 2:
                degree = 1 if sounding_index % 6 == 5 else 0
            elif bar < 4:
                degree = 2 if step >= 12 else (1 if sounding_index % 6 == 5 else 0)
            elif bar < 6:
                degree = [0, 1, 2, 3][sounding_index % 4]
            else:
                degree = [3, 2, 1, 0][sounding_index % 4]
            sounding.append((bar, step, degree, sounding_index))
            sounding_index += 1
    for index, (bar, step, degree, order) in enumerate(sounding):
        start = _step(bar, step)
        if index + 1 < len(sounding):
            gap = _step(sounding[index + 1][0], sounding[index + 1][1]) - start
        else:
            gap = bass_a.container_ticks - start
        velocity = 108 if order % 4 == 0 else 78
        bass_a.add(start, _gate_ok(70, gap, "s04a"), S04[degree], velocity)

    bass_b = _bass(study, "b")
    loop = [7, 8, 9, 8, 7]
    cursor = 0
    chosen = []
    for bar in range(8):
        for beat in range(4):
            if (bar * 4 + beat) % 3 == 2:
                continue
            for sub in range(4):
                chosen.append((bar, beat * 4 + sub, loop[cursor % 5]))
                cursor += 1
    for index, (bar, step, degree) in enumerate(chosen):
        start = _step(bar, step)
        gap = (_step(chosen[index + 1][0], chosen[index + 1][1]) - start) if index + 1 < len(chosen) else bass_b.container_ticks - start
        velocity = 118 if degree == 9 else 96
        bass_b.add(start, _gate_ok(200, gap, "s04b"), S04[degree], velocity)

    harm = _harm(study, _collection(S04))
    add_items(harm, [
        (_step(0, 0), 2 * BAR_TICKS_4_4, S04[0], 46, False),
        (_step(0, 0), 2 * BAR_TICKS_4_4, S04[4], 40, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S04[7], 50, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S04[10], 44, False),
    ])
    kick_a = _kick(study, "a", "kick-a")
    kick_b = _kick(study, "b", "kick-b")
    for bar in range(0, 8, 2):
        kick_a.add(_step(bar, 0), 180, 36, 116)
    for bar in range(8):
        for beat in range(4):
            if (bar * 4 + beat) % 3 == 2:
                kick_b.add(_step(bar, beat * 4), 160, 36, 110)
    return [bass_a, bass_b, harm, kick_a, kick_b]


def _burst(scale, bar, steps, degrees, gate, velocity):
    return [(_step(bar, step), gate, scale[degree], velocity, False) for step, degree in zip(steps, degrees)]


def _s05(study: dict) -> list[Part]:
    bass_a = _bass(study, "a")
    odds = [1, 3, 5, 7, 9, 11, 13, 15]
    add_items(bass_a, [
        _hold(S05, 0, 0, 3, 80),
        *_burst(S05, 3, odds, [0, 4, 0, 4, 0, 4, 0, 4], 100, 104),
        _hold(S05, 4, 4, 3, 76),
        *_burst(S05, 7, odds, [7, 6, 4, 2, 0, 2, 4, 7], 100, 100),
        _hold(S05, 7, 8, 2, 84),
        *_burst(S05, 11, odds, [0, 2, 4, 7, 4, 2, 0, 4], 120, 96),
        _hold(S05, 0, 12, 2, 72),
        (_step(15, 4), 1440, S05[7], 90, False),
    ])
    bass_b = _bass(study, "b")
    sparse = [1, 5, 13]
    add_items(bass_b, [
        _hold(S05, 1, 0, 3, 74),
        *_burst(S05, 3, sparse, [0, 2, 1], 140, 98),
        _hold(S05, 5, 4, 3, 70),
        *_burst(S05, 7, sparse, [1, 0, 2], 140, 96),
        _hold(S05, 8, 8, 2, 78),
        *_burst(S05, 11, sparse, [2, 1, 0], 140, 94),
        _hold(S05, 12, 12, 2, 68),
        (_step(15, 8), 960, S05[1], 88, False),
    ])
    harm = _harm(study, _collection(S05))
    add_items(harm, [
        (_step(4, 0), 2 * BAR_TICKS_4_4, S05[2], 48, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S05[6], 42, False),
        (_step(10, 0), 2 * BAR_TICKS_4_4, S05[8], 50, False),
        (_step(10, 0), 2 * BAR_TICKS_4_4, S05[12], 44, False),
    ])
    kick = _kick(study, "a", "kick-reference")
    for bar in range(16):
        kick.add(_step(bar, 0), 120, 36, 112)
        kick.add(_step(bar, 8), 120, 36, 100)
    return [bass_a, bass_b, harm, kick]


def _s06(study: dict) -> list[Part]:
    cell = [36, 37, 39, 42, 43]
    retro = [43, 42, 39, 37, 36]
    collection = set(cell)
    bass_a = _bass(study, "a")
    bass_a.collection = collection
    slots_a = [step for step in range(16) if step not in (0, 8)]
    pending = []
    for bar in range(8):
        if bar == 7:
            seq = retro
        else:
            rotation = bar % 5
            seq = cell[rotation:] + cell[:rotation]
        for index, step in enumerate(slots_a):
            pitch = seq[index % 5]
            departure = False
            if bar == 6 and step == 4:
                pitch = 41
                departure = True
            pending.append((bar, step, pitch, 80 if bar == 7 else 120, departure))
    for index, (bar, step, pitch, gate, departure) in enumerate(pending):
        start = _step(bar, step)
        gap = (_step(pending[index + 1][0], pending[index + 1][1]) - start) if index + 1 < len(pending) else bass_a.container_ticks - start
        velocity = 112 if step in (4, 12) else 84
        bass_a.add(start, _gate_ok(gate, gap, "s06a"), pitch, velocity, departure=departure)

    bass_b = _bass(study, "b")
    bass_b.collection = collection
    slots_b = [0, 1, 3, 4, 5, 7, 8, 9, 11, 12, 13, 15]
    base = retro[2:] + retro[:2]
    pending = []
    for bar in range(8):
        rotation = bar % 5
        seq = base[rotation:] + base[:rotation]
        for index, step in enumerate(slots_b):
            pitch = seq[index % 5]
            departure = False
            if bar == 3 and step == 4:
                pitch = 44
                departure = True
            pending.append((bar, step, pitch, departure))
    for index, (bar, step, pitch, departure) in enumerate(pending):
        start = _step(bar, step)
        gap = (_step(pending[index + 1][0], pending[index + 1][1]) - start) if index + 1 < len(pending) else bass_b.container_ticks - start
        velocity = 100 if step in (0, 8) else 68
        bass_b.add(start, _gate_ok(70, gap, "s06b"), pitch, velocity, departure=departure)

    harm = _harm(study, collection)
    add_items(harm, [
        (_step(0, 0), 2 * BAR_TICKS_4_4, 36, 48, False),
        (_step(0, 0), 2 * BAR_TICKS_4_4, 42, 42, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, 39, 50, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, 43, 44, False),
    ])
    kick_a = _kick(study, "a", "kick-a")
    kick_b = _kick(study, "b", "kick-b")
    for bar in range(8):
        kick_a.add(_step(bar, 0), 110, 36, 116)
        kick_a.add(_step(bar, 8), 110, 36, 102)
        for step in (2, 6, 10, 14):
            kick_b.add(_step(bar, step), 70, 36, 100)
    return [bass_a, bass_b, harm, kick_a, kick_b]


def _s07(study: dict) -> list[Part]:
    bass_a = _bass(study, "a")
    slots = [0, 1, 2, 4, 5, 8, 9, 10, 12, 13]
    pools = [[0, 1], [0, 1, 2], [0, 1, 2, 4], [0, 1, 2, 4, 6]]
    items = []
    for cycle, pool in enumerate(pools):
        for bar_in in range(2):
            bar = cycle * 4 + bar_in
            for index, step in enumerate(slots):
                degree = pool[(bar_in * len(slots) + index) % len(pool)]
                items.append((_step(bar, step), 140, S07[degree], 116 if step == 0 else 92, False))
        items.append((_step(cycle * 4 + 2, 0), 1920, S07[0], 64, False))
    add_items(bass_a, items)

    bass_b = _bass(study, "b")
    q_slots = [0, 1, 2, 4, 5, 8, 9, 10]
    q_pools = [
        [0, 1],
        [0, 1, 2],
        [0, 1, 2, 4],
        [0, 1, 2, 4, 6],
        [0, 1, 2, 4, 6],
        [7, 8, 9, 11],
        [7, 8, 11, 13],
        [7, 9, 11, 13, 14],
    ]
    answers = [
        [6, 5, 4, 3, 2, 1, 0, 0],
        [6, 5, 4, 3, 2, 1, 0, 0],
        [6, 5, 4, 2, 1, 0, 0, 0],
        [13, 12, 11, 6, 4, 2, 1, 0],
        [13, 12, 11, 10, 6, 4, 2, 0],
        [14, 13, 11, 9, 7, 4, 2, 0],
        [14, 13, 12, 11, 9, 7, 4, 0],
        [14, 11, 9, 7, 6, 4, 2, 0],
    ]
    a_steps = [0, 2, 4, 6, 8, 10, 12, 14]
    items = []
    for pair in range(8):
        pool = q_pools[pair]
        for index, step in enumerate(q_slots):
            degree = pool[index % len(pool)]
            items.append((_step(pair * 2, step), 130, S07[degree], 114 if step == 0 else 88, False))
        for step, degree in zip(a_steps, answers[pair]):
            items.append((_step(pair * 2 + 1, step), 200, S07[degree], 102 if step == 0 else 80, False))
    add_items(bass_b, items)

    harm = _harm(study, _collection(S07))
    add_items(harm, [
        (_step(0, 0), 2 * BAR_TICKS_4_4, S07[0], 50, False),
        (_step(0, 0), 2 * BAR_TICKS_4_4, S07[4], 44, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S07[1], 48, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S07[5], 42, False),
        (_step(8, 0), 2 * BAR_TICKS_4_4, S07[7], 52, False),
        (_step(8, 0), 2 * BAR_TICKS_4_4, S07[13], 46, False),
        (_step(12, 0), 2 * BAR_TICKS_4_4, S07[0], 46, False),
        (_step(12, 0), 2 * BAR_TICKS_4_4, S07[2], 40, False),
    ])
    kick = _kick(study, "a", "kick-reference")
    for cycle in range(4):
        gap_bar = cycle * 4 + 2
        for beat in (2, 3):
            kick.add(_step(gap_bar, beat * 4), 100, 36, 108)
        silent = cycle * 4 + 3
        for beat in range(4):
            kick.add(_step(silent, beat * 4), 100, 36, 116 if beat == 0 else 96)
    return [bass_a, bass_b, harm, kick]


def _s08(study: dict) -> list[Part]:
    bass_a = _bass(study, "a")
    bass_a.collection = _collection(S08)
    steps = [5, 7, 13, 15]
    items = []
    for bar in range(8):
        degrees = [0, 7, 0, 7]
        for index, (step, degree) in enumerate(zip(steps, degrees)):
            departure = False
            pitch = S08[degree]
            if degree == 0 and index == 0 and bar in (2, 3, 6, 7):
                pitch = 33
                departure = True
            velocity = 100 if departure else 112 if degree == 7 else 84
            items.append((_step(bar, step), 200, pitch, velocity, departure))
    add_items(bass_a, items)

    bass_b = _bass(study, "b")
    bass_b.collection = _collection(S08)
    steps_b = [1, 7, 9, 15]
    items = []
    for bar in range(8):
        degrees = [0, 4, 0, 4]
        for index, (step, degree) in enumerate(zip(steps_b, degrees)):
            departure = False
            pitch = S08[degree]
            if degree == 4 and index == 3 and bar % 2 == 1:
                pitch = 47
                departure = True
            velocity = 96 if departure else 108 if degree == 0 else 90
            items.append((_step(bar, step), 200, pitch, velocity, departure))
    add_items(bass_b, items)

    harm = _harm(study, _collection(S08))
    add_items(harm, [
        (_step(0, 0), 2 * BAR_TICKS_4_4, S08[0], 50, False),
        (_step(0, 0), 2 * BAR_TICKS_4_4, S08[4], 44, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S08[3], 48, False),
        (_step(4, 0), 2 * BAR_TICKS_4_4, S08[6], 42, False),
        (_step(6, 0), BAR_TICKS_4_4, S08[7], 52, False),
        (_step(6, 0), BAR_TICKS_4_4, S08[9], 46, False),
    ])
    kick = _kick(study, "a", "kick-reference")
    for bar in range(8):
        kick.add(_step(bar, 0), 90, 36, 114)
        kick.add(_step(bar, 8), 90, 36, 102)
    return [bass_a, bass_b, harm, kick]


BUILDERS = {
    "s01": _s01,
    "s02": _s02,
    "s03": _s03,
    "s04": _s04,
    "s05": _s05,
    "s06": _s06,
    "s07": _s07,
    "s08": _s08,
}


def _signature(notes: list[dict]) -> tuple:
    return tuple((note["performed_start"], note["pitch"], note["duration"], note["velocity"]) for note in notes)


def _intervals(notes: list[dict]) -> tuple:
    pitches = [note["pitch"] for note in notes]
    return tuple(b - a for a, b in zip(pitches, pitches[1:]))


def _rhythm(notes: list[dict]) -> tuple:
    return tuple(note["performed_start"] for note in notes)


def assert_identities(parts: list[dict]) -> dict:
    by_study: dict[str, dict[str, dict]] = {}
    for part in parts:
        if part["role"] != "bassline":
            continue
        by_study.setdefault(part["study_id"], {})[part["variation"]] = part
    if len(by_study) != 8:
        raise ValueError("expected 8 studies")
    report = []
    interval_sets = []
    rhythm_sets = []
    for study_id, variations in by_study.items():
        if set(variations) != {"a", "b"}:
            raise ValueError(f"{study_id} variations {set(variations)}")
        sig_a = _signature(variations["a"]["notes"])
        sig_b = _signature(variations["b"]["notes"])
        if sig_a == sig_b:
            raise ValueError(f"{study_id} variations are identical")
        intervals_a = _intervals(variations["a"]["notes"])
        rhythm_a = _rhythm(variations["a"]["notes"])
        interval_sets.append((study_id, intervals_a))
        rhythm_sets.append((study_id, rhythm_a))
        report.append({
            "study_id": study_id,
            "variation_a_notes": len(sig_a),
            "variation_b_notes": len(sig_b),
            "signatures_differ": True,
        })
    for i, (left_id, left_intervals) in enumerate(interval_sets):
        for right_id, right_intervals in interval_sets[i + 1:]:
            if left_intervals == right_intervals and rhythm_sets[i][1] == dict(rhythm_sets)[right_id]:
                raise ValueError(f"{left_id} repeats the contour and rhythm of {right_id}")
    return {"studies": report, "method": "variation signatures differ; study interval-and-rhythm pairs are not duplicated"}


def compose() -> dict:
    catalog_studies = studies()
    parts = []
    for study in catalog_studies:
        for part in BUILDERS[study["id"]](study):
            parts.append(part.finish())
    identity = assert_identities(parts)
    core = [part for part in parts if part["core"]]
    references = [part for part in parts if not part["core"]]
    if len(core) != 16:
        raise ValueError(f"core count {len(core)}")
    preview_ids = ["s01.bass.a", "s01.harmonic", "s01.kick.a"]
    preview_parts = [part for part in parts if part["id"] in preview_ids]
    if [part["id"] for part in preview_parts] != preview_ids:
        # dict order follows composition order; select explicitly
        preview_parts = [next(part for part in parts if part["id"] == part_id) for part_id in preview_ids]
    arrangement = {
        "id": "arrangement-preview-s01a",
        "path": "midi/arrangement.mid",
        "format": 1,
        "container_ticks": 16 * BAR_TICKS_4_4,
        "bpm": 140,
        "tempo_us": bpm_to_us(140),
        "meter": "4/4",
        "description": "Study 01 variation A bassline with its harmonic reference and kick-a. This is the preview arrangement, not a stack of every study.",
        "tracks": [
            {"name": "Conductor", "source_part": None, "channel": None},
            {"name": "Bassline", "source_part": "s01.bass.a", "channel": 0},
            {"name": "Harmonic Reference", "source_part": "s01.harmonic", "channel": 1},
            {"name": "Kick Reference", "source_part": "s01.kick.a", "channel": 9},
        ],
    }
    catalog = {
        "pack_id": PACK_ID,
        "pack_name": PACK_NAME,
        "catalog_version": GENERATOR_VERSION,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "meter": {"numerator": 4, "denominator": 4, "bar_ticks": BAR_TICKS_4_4},
        "pitched_range": [PITCH_LO, PITCH_HI],
        "c4": 60,
        "note_policy": "note-only MIDI; no program changes, controllers, pitch bend, aftertouch, keyswitches, SysEx, or tuning messages",
        "microtiming": "offset is 0 for every note; performed_start = nominal_start + offset",
        "stochastic_draws": 0,
        "seed_meaning": "Seeds identify studies. The compositions are fully specified and do not draw random values.",
        "core_part_count": len(core),
        "reference_part_count": len(references),
        "studies": [
            {
                key: study[key]
                for key in (
                    "id", "slug", "title", "bpm", "tempo_us", "effective_bpm", "bars", "meter",
                    "bar_ticks", "tonic", "tonal_reference", "collection_name", "pitch_classes",
                    "departures", "seed", "identity", "limitations", "stochastic_draws",
                )
            }
            for study in catalog_studies
        ],
        "parts": [
            {
                "id": part["id"],
                "study_id": part["study_id"],
                "role": part["role"],
                "variation": part["variation"],
                "core": part["core"],
                "channel": part["channel"],
                "path": part["path"],
                "notes": len(part["notes"]),
                "container_bars": part["container_bars"],
                "bpm": part["bpm"],
                "monophonic": part["monophonic"],
            }
            for part in parts
        ],
        "arrangement": arrangement,
        "preview_part_ids": preview_ids,
        "stack_warning": "Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.",
    }
    score = {
        "pack_id": PACK_ID,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "parts": parts,
        "arrangement": arrangement,
        "identity_check": identity,
    }
    return {"catalog": catalog, "score": score}
