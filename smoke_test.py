from dotenv import load_dotenv
load_dotenv()

from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='b')
text = "If you can hear this clearly, your Kokoro setup is working."
for i, (gs, ps, audio) in enumerate(pipeline(text, voice='bf_emma')):
    sf.write(f"smoke_{i}.wav", audio, 24000)
print("Wrote smoke_0.wav - open it and listen.")
