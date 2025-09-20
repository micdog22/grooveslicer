
import os, typer, math, io, base64
from typing import Optional
import numpy as np
import soundfile as sf
import librosa
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
from jinja2 import Template
import matplotlib.pyplot as plt

app = typer.Typer(add_completion=False)

def save_midi_click(path: str, tempo_bpm: float, n_beats: int, ppq: int = 480):
    mid = MidiFile(ticks_per_beat=ppq)
    track = MidiTrack()
    mid.tracks.append(track)
    microsec_per_beat = int(60_000_000 / max(tempo_bpm, 1e-6))
    track.append(MetaMessage('set_tempo', tempo=microsec_per_beat, time=0))
    for i in range(n_beats):
        vel = 100 if (i % 4 == 0) else 70
        track.append(Message('note_on', note=37, velocity=vel, time=0))
        track.append(Message('note_off', note=37, velocity=0, time=ppq))
    mid.save(path)

def plot_wave(y, sr):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(y)
    bio = io.BytesIO()
    fig.savefig(bio, format="png", bbox_inches="tight", dpi=140)
    plt.close(fig)
    return base64.b64encode(bio.getvalue()).decode("ascii")

def report_html(audio_path: str, y, sr, beats):
    tmpl = Template("""<!doctype html><html><head><meta charset="utf-8"><title>GrooveSlicer</title></head>
<body><h1>Relatório GrooveSlicer</h1>
<p>Arquivo: {{name}}</p>
<p>BPM estimado: {{bpm}}</p>
<img src="data:image/png;base64,{{png}}">
<p>Beats: {{n}}</p>
</body></html>""")
    png = plot_wave(y, sr)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tmpl.render(name=os.path.basename(audio_path), bpm=f"{tempo:.2f}", png=png, n=len(beats))

@app.command()
def analyze(audio: str, report: bool = typer.Option(False, help="Gerar relatório HTML")):
    y, sr = librosa.load(audio, sr=None, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    typer.echo(f"BPM: {tempo:.2f}, beats: {len(beats)}")
    if report:
        html = report_html(audio, y, sr, beats)
        out = os.path.join("reports", os.path.splitext(os.path.basename(audio))[0] + "_groove.html")
        os.makedirs("reports", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        typer.echo(f"Relatório: {out}")

@app.command()
def slice(audio: str, bars: int = 1, out: str = "slices", midi_click: bool = False, crossfade: float = 0.005):
    y, sr = librosa.load(audio, sr=None, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    os.makedirs(out, exist_ok=True)
    beat_times = beats
    beats_per_bar = 4
    samples = len(y)
    idx = 0
    exported = 0
    for i in range(0, len(beat_times) - beats_per_bar * bars, beats_per_bar * bars):
        t0 = beat_times[i]
        t1 = beat_times[i + beats_per_bar * bars] if i + beats_per_bar * bars < len(beat_times) else beat_times[-1]
        s0 = int(t0 * sr)
        s1 = int(t1 * sr)
        chunk = y[s0:s1]
        # crossfade edges
        cf = int(crossfade * sr)
        if cf > 0 and len(chunk) > 2*cf:
            fade = np.linspace(0,1,cf)
            chunk[:cf] *= fade
            chunk[-cf:] *= fade[::-1]
        dest = os.path.join(out, f"loop_{i//(beats_per_bar*bars):04d}.wav")
        sf.write(dest, chunk, sr)
        exported += 1
    typer.echo(f"Loops exportados: {exported}")
    if midi_click:
        total_beats = len(beat_times)
        midi_path = os.path.join(out, "click.mid")
        save_midi_click(midi_path, tempo, total_beats)
        typer.echo(f"MIDI do clique: {midi_path}")

@app.command()
def quantize(audio: str, strength: float = 0.5, out: str = "quantized.wav"):
    y, sr = librosa.load(audio, sr=None, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    beat_frames = beats
    hop = 512
    times = librosa.frames_to_samples(beat_frames, hop_length=hop)
    # Simple stretch: snap beat frames to uniform grid
    if len(times) < 2:
        sf.write(out, y, sr); return
    target_interval = int(np.median(np.diff(times)))
    new = y.copy()
    for i in range(1, len(times)-1):
        cur = times[i]
        ideal = times[0] + i * target_interval
        shift = int((ideal - cur) * strength)
        a = cur - target_interval//2
        b = cur + target_interval//2
        a = max(0, a); b = min(len(y), b)
        seg = new[a:b]
        pad = np.zeros_like(seg)
        if shift > 0:
            seg = np.concatenate([np.zeros(shift), seg[:-shift]])
        elif shift < 0:
            seg = np.concatenate([seg[-shift:], np.zeros(-shift)])
        new[a:b] = 0.5*new[a:b] + 0.5*seg[:b-a]
    sf.write(out, new, sr)
    typer.echo(f"Arquivo quantizado: {out}")

if __name__ == "__main__":
    app()
