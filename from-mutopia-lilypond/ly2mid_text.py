"""LilyPond で .ly から .mid を作り、MIDI に反映されない記号を text meta event として書き足す。

使い方: python ly2mid_text.py <file.ly> [--lilypond <lilypond.exe>]
.mid は .ly と同じ場所に、LilyPond 既定の名前で出る。
--tempo-only は既存 .mid のテンポ情報だけを補う（LilyPond 不要）。
"""
import argparse
from collections import Counter
import json
import subprocess
from pathlib import Path

import mido

SETTINGS = Path(__file__).with_name("midi-text-events.ly")

# 四分音符基準の代表値。標準・確定値ではなく、演奏意図に応じて調整する。
# 大小関係を保つため、修飾を含む指定は単語に分割せず全体で登録する。
TEMPO_BPMS = {
    "larghissimo": 24, "adagissimo": 40, "grave": 40, "largo": 40,
    "larghetto": 50, "lento": 50, "molto adagio": 40, "adagio": 60,
    "adagietto": 72, "andante": 80, "andantino": 88, "moderato": 100,
    "allegretto": 112, "allegro moderato": 116, "allegro": 120,
    "allegro vivace": 144, "vivace": 160, "vivacissimo": 176,
    "presto": 180, "prestissimo": 200,
}
# 選択式と確認した組み合わせのみ登録する。候補ごとの値も代表値。
TEMPO_CHOICES = {"adagio vivace": (("Adagio", 40), ("Vivace", 160))}
FREE_TEMPOS = {"recitativo": "Recitativo : free tempo"}
# 速度指定でない既知のtext。その他の未知のtextは未変換として報告する。
NON_TEMPO_TEXTS = {
    "fermata", "arpeggio", "mordent", "prall", "trill", "staccato",
    "staccatissimo", "tenuto", "accent", "marcato", "portato", "breath",
}
GENERATED_PREFIX = b"ly2mid-tempo-v1:"
DEFAULT_MARKER = "ly2mid: initial tempo is LilyPond default"
NUMERIC_MARKER = "ly2mid: explicit numeric tempo"


def normalize(text):
    return " ".join(text.casefold().split())


def absolute_events(track):
    tick = 0
    for msg in track:
        tick += msg.time
        yield tick, msg


def replace_track(track, events):
    # 指揮trackが短いMIDIでも、追加イベントの後までend_of_trackを延ばす。
    end = max((tick for tick, _ in events), default=0)
    events = [(end if msg.type == "end_of_track" else tick, msg)
              for tick, msg in events]
    events.sort(key=lambda item: (item[0], item[1].type == "end_of_track"))
    track.clear()
    previous = 0
    for tick, msg in events:
        track.append(msg.copy(time=tick - previous))
        previous = tick


def apply_tempos(mid):
    """共通の代表値で補完し、元の数値指定・textを保つ。曲名には依存しない。"""
    if mid.type == 2:
        raise ValueError("独立した時間軸を持つSMF type 2には対応していません")
    tracks = [list(absolute_events(track)) for track in mid.tracks]
    conductor = tracks[0]
    # 前回追加したものだけを除去し、元のテンポへ戻してから計算し直す。
    # メタ情報を持たない数値指定は、出所不明でも明示値として保護する。
    owned = Counter()
    restored = []
    generated_texts = Counter()
    for tick, msg in conductor:
        if msg.type == "sequencer_specific" and bytes(msg.data).startswith(GENERATED_PREFIX):
            record = json.loads(bytes(msg.data)[len(GENERATED_PREFIX):])
            if "tempo" in record:
                owned[tick, record["tempo"]] += 1
            for tempo in record.get("replaced", []):
                restored.append((tick, mido.MetaMessage("set_tempo", tempo=tempo)))
            for text in record.get("texts", []):
                generated_texts[tick, text] += 1
    original = []
    for tick, msg in conductor:
        if msg.type == "sequencer_specific" and bytes(msg.data).startswith(GENERATED_PREFIX):
            continue
        if msg.type == "set_tempo" and owned[tick, msg.tempo]:
            owned[tick, msg.tempo] -= 1
            continue
        if msg.type == "text" and generated_texts[tick, msg.text]:
            generated_texts[tick, msg.text] -= 1
            continue
        original.append((tick, msg))
    conductor = original + restored
    tracks[0] = conductor

    existing = {}
    wanted = {}
    hints = {}
    unresolved = set()
    initial_default = any(msg.type == "text" and msg.text == DEFAULT_MARKER
                          for _, msg in conductor)
    explicit_ticks = {tick for track in tracks for tick, msg in track
                      if msg.type == "text" and msg.text == NUMERIC_MARKER}
    for track in tracks:
        for tick, msg in track:
            if msg.type == "set_tempo":
                # 初期値という出所が記録された60だけは、文字指定で置換可能。
                if initial_default and tick == 0 and tick not in explicit_ticks and msg.tempo == 1000000:
                    continue
                if tick in existing and existing[tick] != msg.tempo:
                    raise ValueError(f"同じtickに異なる数値テンポ: {tick}")
                existing[tick] = msg.tempo
            elif msg.type == "text":
                text = normalize(msg.text)
                if text in TEMPO_BPMS:
                    candidates = ((msg.text, TEMPO_BPMS[text]),)
                elif text in TEMPO_CHOICES:
                    candidates = TEMPO_CHOICES[text]
                else:
                    if text in FREE_TEMPOS:
                        hints.setdefault(tick, set()).add(FREE_TEMPOS[text])
                    if (text and text not in NON_TEMPO_TEXTS
                            and not text.startswith(("ly2mid:", "creator:", "lilypond "))):
                        unresolved.add((tick, msg.text))
                    continue
                values = tuple(bpm for _, bpm in candidates)
                if tick in wanted and wanted[tick] != values:
                    raise ValueError(f"同じtickに異なる文字テンポ: {tick}")
                wanted[tick] = values
                if text in TEMPO_CHOICES:
                    options = " | ".join(f"{name} (quarter BPM={bpm})" for name, bpm in candidates)
                    hints.setdefault(tick, set()).add(f"tempo alternatives: {options}; performer choice")

    current_bpm = 120  # set_tempoがない場合のSMF既定値
    count = 0
    for tick in sorted(existing.keys() | wanted.keys() | hints.keys()):
        record = {"texts": sorted(hints.get(tick, set()))}
        if tick in existing:
            current_bpm = mido.tempo2bpm(existing[tick])
        elif tick in wanted:
            current_bpm = min(wanted[tick], key=lambda bpm: (abs(bpm - current_bpm), bpm))
            record["tempo"] = mido.bpm2tempo(current_bpm)
            record["replaced"] = []
            if tick == 0 and initial_default and tick not in explicit_ticks:
                record["replaced"] = [msg.tempo for t, msg in conductor
                                      if t == tick and msg.type == "set_tempo"]
                conductor[:] = [(t, msg) for t, msg in conductor
                                if not(t == tick and msg.type == "set_tempo")]
            conductor.append((tick, mido.MetaMessage("set_tempo", tempo=record["tempo"])))
            count += 1
        for text in record["texts"]:
            conductor.append((tick, mido.MetaMessage("text", text=text)))
        if "tempo" in record or record["texts"]:
            payload = GENERATED_PREFIX + json.dumps(record, ensure_ascii=True, sort_keys=True).encode("ascii")
            conductor.append((tick, mido.MetaMessage("sequencer_specific", data=tuple(payload))))
    replace_track(mid.tracks[0], conductor)
    return count, sorted(unresolved)


def read_events(tsv):
    for line in tsv.read_text(encoding="utf-8").splitlines():
        moment, ids, kind, value = line.split("\t")
        yield float(moment), ids.split(","), kind, value


def inject(mid_path, events):
    mid = mido.MidiFile(mid_path)
    ticks_per_whole = mid.ticks_per_beat * 4
    track_by_id = {}
    for track in mid.tracks:
        for msg in track:
            if msg.type == "track_name":
                track_by_id[msg.name.rstrip(":")] = track
                break

    wanted = {}  # track -> {(tick, text)}  同時刻・同文字列は声部をまたいで1つにまとめる
    for moment, ids, kind, value in events:
        text = NUMERIC_MARKER if kind == "tempo-numeric" else value or kind
        if ids == [""]:  # Score 宛て（\tempo）は set_tempo と同じ指揮 track へ
            track = mid.tracks[0]
        else:
            track = next((track_by_id[i] for i in ids if i in track_by_id), None)
        if track is None:
            raise SystemExit(f"track が見つからない: {ids}")
        wanted.setdefault(id(track), (track, set()))[1].add((round(moment * ticks_per_whole), text))

    for track, items in wanted.values():
        absolute = list(absolute_events(track))
        absolute += [(t, mido.MetaMessage("text", text=s)) for t, s in sorted(items)]
        replace_track(track, absolute)
    mid.save(mid_path)
    return sum(len(items) for _, items in wanted.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ly", type=Path)
    ap.add_argument("--lilypond", default="lilypond")
    ap.add_argument("--tempo-only", action="store_true", help="既存MIDIのテンポ情報だけを補う")
    args = ap.parse_args()

    ly = args.ly.resolve()
    out = ly.with_suffix("")
    mid_path = ly.with_suffix(".mid")
    if not args.tempo_only:
        tsv = Path(f"{out}.text-events.tsv")
        tsv.unlink(missing_ok=True)  # performer が追記するため
        subprocess.run(
            [args.lilypond, f"-dinclude-settings={SETTINGS}", "-o", str(out), ly.name],
            cwd=ly.parent,
            check=True,
        )
        events = list(read_events(tsv)) if tsv.exists() else []
        tsv.unlink(missing_ok=True)
        print(f"text meta event {inject(mid_path, events)} 件を書き足した")
    mid = mido.MidiFile(mid_path)
    if not args.tempo_only:
        # LilyPond既定値は数値指定と区別して残す。既存MIDI単体では推測しない。
        numeric_at_start = any(moment == 0 and kind == "tempo-numeric"
                               for moment, _, kind, _ in events)
        if not numeric_at_start and any(t == 0 and msg.type == "set_tempo" and msg.tempo == 1000000
                                        for t, msg in absolute_events(mid.tracks[0])):
            mid.tracks[0].insert(0, mido.MetaMessage("text", text=DEFAULT_MARKER))
    count, unresolved = apply_tempos(mid)
    mid.save(mid_path)
    print(f"代表BPMによる set_tempo {count} 件、候補・演奏ヒントをtextに記録した")
    for tick, text in unresolved:
        print(f"未変換 tick={tick}: {text}")


if __name__ == "__main__":
    main()
