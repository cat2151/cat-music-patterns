import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import mido

import ly2mid_text as converter


def midi(events, *, default=False, tempo=60):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    absolute = [(0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo)))]
    if default:
        absolute.append((0, mido.MetaMessage("text", text=converter.DEFAULT_MARKER)))
    absolute.extend((tick, mido.MetaMessage("text", text=text)) for tick, text in events)
    absolute.append((max([tick for tick, _ in events] + [0]) + 384,
                     mido.MetaMessage("end_of_track")))
    converter.replace_track(track, absolute)
    return mid


def tempos(mid):
    return {tick: msg.tempo for track in mid.tracks
            for tick, msg in converter.absolute_events(track) if msg.type == "set_tempo"}


def dump(mid):
    output = io.BytesIO()
    mid.save(file=output)
    return output.getvalue()


class TempoConversionTests(unittest.TestCase):
    def test_common_words_and_compound_meaning(self):
        mid = midi([(0, " LARGO "), (384, "Andante"), (768, "Allegro moderato"),
                    (1152, "Allegro"), (1536, "Vivace"), (1920, "Presto"),
                    (2304, "Prestissimo")], default=True)
        converter.apply_tempos(mid)
        expected = [40, 80, 116, 120, 160, 180, 200]
        self.assertEqual(list(tempos(mid).values()), [mido.bpm2tempo(n) for n in expected])
        self.assertEqual(expected, sorted(expected))

    def test_choices_and_recalculation(self):
        mid = midi([(384, "Presto"), (768, "Adagio Vivace")])
        converter.apply_tempos(mid)
        self.assertEqual(tempos(mid)[768], mido.bpm2tempo(160))
        initial = dump(mid)
        converter.apply_tempos(mid)
        self.assertEqual(dump(mid), initial)
        # 追加済みのテンポを明示値と誤認せず、直前の代表値変更を反映する。
        with patch.dict(converter.TEMPO_BPMS, {"presto": 60}):
            converter.apply_tempos(mid)
        self.assertEqual(tempos(mid)[384], mido.bpm2tempo(60))
        self.assertEqual(tempos(mid)[768], mido.bpm2tempo(40))
        all_text = [msg.text for tr in mid.tracks for msg in tr if msg.type == "text"]
        self.assertEqual(sum(text.startswith("tempo alternatives:") for text in all_text), 1)

    def test_choice_tie_prefers_slower(self):
        mid = midi([(384, "Adagio Vivace")], tempo=100)
        converter.apply_tempos(mid)
        self.assertEqual(tempos(mid)[384], mido.bpm2tempo(40))

    def test_unknown_and_free_tempo_keep_notes_and_text(self):
        mid = midi([(384, "Recitativo"), (768, "rit."), (1152, "Allegro misterioso")])
        mid.tracks.append(mido.MidiTrack([
            mido.Message("note_on", note=60, velocity=64, time=120),
            mido.Message("note_off", note=60, time=240),
            mido.MetaMessage("end_of_track")]))
        notes = list(mid.tracks[1])
        _, unresolved = converter.apply_tempos(mid)
        self.assertEqual(unresolved, [(384, "Recitativo"), (768, "rit."), (1152, "Allegro misterioso")])
        self.assertEqual(tempos(mid), {0: mido.bpm2tempo(60)})
        self.assertEqual(list(mid.tracks[1]), notes)
        self.assertIn((384, "Recitativo : free tempo"), [
            (tick, msg.text) for tick, msg in converter.absolute_events(mid.tracks[0])
            if msg.type == "text"])
        once = dump(mid)
        converter.apply_tempos(mid)
        self.assertEqual(dump(mid), once)

    def test_explicit_numeric_and_unknown_origin_are_preserved(self):
        for default, explicit in [(False, False), (True, True)]:
            mid = midi([(0, "Largo")], default=default)
            if explicit:
                mid.tracks[0].insert(0, mido.MetaMessage("text", text=converter.NUMERIC_MARKER))
            converter.apply_tempos(mid)
            self.assertEqual(tempos(mid)[0], mido.bpm2tempo(60))

    def test_conflicting_text_fails_without_mutation(self):
        mid = midi([(384, "Adagio"), (384, "Presto")])
        before = dump(mid)
        with self.assertRaises(ValueError):
            converter.apply_tempos(mid)
        self.assertEqual(dump(mid), before)

    def test_short_conductor_extends_to_later_events(self):
        mid = midi([])
        mid.tracks.append(midi([(1536, "Andante")]).tracks[0])
        converter.apply_tempos(mid)
        end, msg = list(converter.absolute_events(mid.tracks[0]))[-1]
        self.assertEqual(msg.type, "end_of_track")
        self.assertGreaterEqual(end, 1536)
        loaded = mido.MidiFile(file=io.BytesIO(dump(mid)))
        self.assertEqual(tempos(loaded)[1536], mido.bpm2tempo(80))

    def test_any_filename_and_generation_numeric_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "AnotherPiece.ly"
            source.write_text("", encoding="utf-8")
            output = source.with_suffix(".mid")
            for explicit, expected in [(False, 40), (True, 60)]:
                def compile_stub(*args, **kwargs):
                    midi([]).save(output)
                    lines = "0\t\ttempo\tLargo\n"
                    if explicit:
                        lines += "0\t\ttempo-numeric\t\n"
                    source.with_suffix(".text-events.tsv").write_text(lines, encoding="utf-8")
                with patch.object(sys, "argv", ["ly2mid_text.py", str(source)]), \
                     patch.object(converter.subprocess, "run", side_effect=compile_stub):
                    converter.main()
                self.assertEqual(tempos(mido.MidiFile(output))[0], mido.bpm2tempo(expected))
                original = output.read_bytes()
                with patch.object(sys, "argv", ["ly2mid_text.py", str(source), "--tempo-only"]):
                    converter.main()
                self.assertEqual(output.read_bytes(), original)

    def test_independent_sequences_are_rejected(self):
        mid = midi([])
        mid.type = 2
        with self.assertRaises(ValueError):
            converter.apply_tempos(mid)


if __name__ == "__main__":
    unittest.main()
