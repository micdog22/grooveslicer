# GrooveSlicer — Beat Slicing, Tempo Map & Quantize

GrooveSlicer detecta BPM, cria mapa de tempo, alinha a grade e fatia o áudio por compassos/beat. Exporta loops prontos, cliques MIDI e um relatório simples.

## Funcionalidades
- Detecção de BPM e mapa de tempo.
- Slicing por beat/compasso, com crossfade e normalização.
- Quantização de transientes (ajuste por estiramento de trechos).
- Export de clique MIDI e de lista de cortes.
- Relatório HTML com formas de onda e anotação de beats básicos.

## Instalação
Requisitos: Python 3.10+, FFmpeg.
```bash
pip install -r requirements.txt
```

## Uso
```bash
# analisar BPM e beats
python src/grooveslicer.py analyze audio/minha_track.wav --report

# fatiar por compassos com 1-bar loops e criar MIDI de clique
python src/grooveslicer.py slice audio/minha_track.wav --bars 1 --midi-click --out slices

# quantizar trechos para grid (experimental)
python src/grooveslicer.py quantize audio/minha_track.wav --strength 0.5 --out quantized.wav
```

## Limitações
Quantização destrutiva pode introduzir artefatos. Ajuste `--strength` e revise os resultados.

## Licença
MIT.
