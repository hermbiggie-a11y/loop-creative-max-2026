"""Narration lines in Logan's cloned voice (Chatterbox, local GPU).
   python narrate.py lines.json out_dir     lines.json = [{"id": "n001", "text": "..."}]; existing wavs are kept."""
import json, os, sys, torch, torchaudio as ta
from pathlib import Path
from chatterbox.tts import ChatterboxTTS

here = Path(__file__).parent
lines = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
todo = [l for l in lines if not (out / f"{l['id']}.wav").exists()]
if todo:
    m = ChatterboxTTS.from_pretrained(device="cuda")
    for l in todo:
        torch.manual_seed(l.get("seed", 1))
        wav = m.generate(l["text"], audio_prompt_path=os.environ.get("REF", str(here / "samples" / "ref.wav")),
                         exaggeration=l.get("ex", 0.5), cfg_weight=l.get("cfg", 0.5))
        ta.save(str(out / f"{l['id']}.wav"), wav, m.sr)
        print(l["id"], round(wav.shape[-1] / m.sr, 2), flush=True)
for l in lines:
    i = ta.info(str(out / f"{l['id']}.wav")); print("dur", l["id"], round(i.num_frames / i.sample_rate, 2))
