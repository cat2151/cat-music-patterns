"""LilyPond で .ly から .mid を作り、MIDI に反映されない記号を text meta event として書き足す。

使い方: python ly2mid_text.py <file.ly> [--lilypond <lilypond.exe>]
.mid は .ly と同じ場所に、LilyPond 既定の名前で出る。
"""
import argparse
import subprocess
from pathlib import Path

import mido

SETTINGS = Path(__file__).with_name("midi-text-events.ly")


def read_events(tsv):
    for line in tsv.read_text(encoding="utf-8").splitlines():
        moment, ids, kind, value = line.split("\t")
        yield float(moment), ids.split(","), value or kind


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
    for moment, ids, text in events:
        if ids == [""]:  # Score 宛て（\tempo）は set_tempo と同じ指揮 track へ
            track = mid.tracks[0]
        else:
            track = next((track_by_id[i] for i in ids if i in track_by_id), None)
        if track is None:
            raise SystemExit(f"track が見つからない: {ids}")
        wanted.setdefault(id(track), (track, set()))[1].add((round(moment * ticks_per_whole), text))

    for track, items in wanted.values():
        absolute, tick = [], 0
        for msg in track:
            tick += msg.time
            absolute.append((tick, msg))
        end = absolute.pop()  # end_of_track は末尾に残す
        absolute += [(t, mido.MetaMessage("text", text=s)) for t, s in sorted(items)]
        absolute.sort(key=lambda x: x[0])  # 安定ソート: 同 tick では元の event が先
        absolute.append(end)
        track.clear()
        prev = 0
        for t, msg in absolute:
            track.append(msg.copy(time=t - prev))
            prev = t
    mid.save(mid_path)
    return sum(len(items) for _, items in wanted.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ly", type=Path)
    ap.add_argument("--lilypond", default="lilypond")
    args = ap.parse_args()

    ly = args.ly.resolve()
    out = ly.with_suffix("")
    tsv = Path(f"{out}.text-events.tsv")
    tsv.unlink(missing_ok=True)  # performer が追記するため
    subprocess.run(
        [args.lilypond, f"-dinclude-settings={SETTINGS}", "-o", str(out), ly.name],
        cwd=ly.parent,
        check=True,
    )
    events = list(read_events(tsv)) if tsv.exists() else []
    tsv.unlink(missing_ok=True)
    print(f"text meta event {inject(f'{out}.mid', events)} 件を書き足した")


if __name__ == "__main__":
    main()
