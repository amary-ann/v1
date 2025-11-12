import librosa
import numpy as np

def detect_gender_from_audio(audio_chunk):
    # Convert audio chunk to numpy array for pitch analysis
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)

    # Normalize audio (librosa expects float32 between -1 and 1)
    audio_data /= np.max(np.abs(audio_data), initial=1.0)

    try:
        # Use YIN pitch detection (more robust than piptrack for monophonic voice)
        pitches = librosa.yin(audio_data, fmin=75, fmax=300, sr=16000)

        # Filter out NaNs and very low magnitudes
        pitches = pitches[~np.isnan(pitches)]
        if len(pitches) == 0:
            return "UNKNOWN"

        avg_pitch = np.mean(pitches)
        print(f"Average Pitch: {avg_pitch:.2f} Hz")

        # Gender classification based on pitch
        if avg_pitch < 165:
            return "MALE"
        else:
            return "FEMALE"

    except Exception as e:
        print("Pitch detection error:", e)
        return "UNKNOWN"


# import torch

# from model import ECAPA_gender

# # You could directly download the model from the huggingface model hub
# model = ECAPA_gender.from_pretrained("JaesungHuh/voice-gender-classifier")
# model.eval()

# # If you are using gpu .... 
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# model.to(device)

# # Load the audio file and use predict function to directly get the output
# example_file = "gender_detect_mary.wav"
# with torch.no_grad():
#     output = model.predict(example_file, device=device)
#     print("Gender : ", output)
