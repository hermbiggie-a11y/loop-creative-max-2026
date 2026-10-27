"""Generate voice-clone takes from Logan's reference read (Chatterbox, local GPU)."""
import sys, torch, torchaudio as ta
from pathlib import Path
from chatterbox.tts import ChatterboxTTS
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

here = Path(__file__).parent
ref = str(here / "samples" / "ref.wav")
out = here / "takes"; out.mkdir(exist_ok=True)

EN = ("Miami wakes up slow. The sun hits the sand, the water turns teal, and somebody cracks a can. "
      "Cabana Cold Brew. Twenty hours of steeping, poured over ice, sealed cold. Smooth, a little sweet, never bitter. "
      "From the first swim to the last set, it keeps up with you. Cabana Cold Brew. Sunshine in a can. Now in Miami.")
ES = "Cabana Cold Brew. Sol en una lata. Ya en la Pequeña Habana."

what = sys.argv[1] if len(sys.argv) > 1 else "both"
if what in ("en", "both"):
    m = ChatterboxTTS.from_pretrained(device="cuda")
    for i, (ex, cfg) in enumerate([(0.5, 0.5), (0.4, 0.4), (0.6, 0.3)], 1):
        torch.manual_seed(i)
        wav = m.generate(EN, audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg)
        ta.save(str(out / f"en-take{i}.wav"), wav, m.sr)
        print("en", i, wav.shape[-1] / m.sr, "s", flush=True)
    del m; torch.cuda.empty_cache()
if what in ("es", "both"):
    m = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
    for i in (1, 2, 3):
        torch.manual_seed(i)
        wav = m.generate(ES, language_id="es", audio_prompt_path=ref, exaggeration=0.5, cfg_weight=0.5)
        ta.save(str(out / f"es-take{i}.wav"), wav, m.sr)
        print("es", i, wav.shape[-1] / m.sr, "s", flush=True)
