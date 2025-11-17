import whisper
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer



def transcribe_video(video_path):
    print("Transcribing video...")
    model = whisper.load_model("medium")
    result = model.transcribe(video_path)
    return result["text"]



def compute_bleu(reference_text, hypothesis_text):
    reference = [reference_text.split()]
    hypothesis = hypothesis_text.split()

    smoothie = SmoothingFunction().method4
    bleu = sentence_bleu(reference, hypothesis, smoothing_function=smoothie)
    return bleu



def compute_rouge(reference_text, hypothesis_text):
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference_text, hypothesis_text)
    return scores



def evaluate_video(reference_script_path, video_path):
    # Load reference script (the text your TTS read)
    with open(reference_script_path, "r", encoding="utf-8") as f:
        reference = f.read().strip()

    # Extract spoken text from video
    hypothesis = transcribe_video(video_path)

    # Compute metrics
    bleu = compute_bleu(reference, hypothesis)
    rouge = compute_rouge(reference, hypothesis)

    return {
        "BLEU": bleu,
        "ROUGE-1": rouge["rouge1"].fmeasure,
        "ROUGE-2": rouge["rouge2"].fmeasure,
        "ROUGE-L": rouge["rougeL"].fmeasure,
        "transcribed_text": hypothesis
    }



if __name__ == "__main__":
    metrics = evaluate_video(
        reference_script_path="content_ch1s/data_processing_at_scale/script.md",
        video_path="final_notebooklms/What_is_Data_Mining_.mp4"
    )

    print("\n=== Evaluation Metrics ===")
    print("BLEU:", metrics["BLEU"])
    print("ROUGE-1:", metrics["ROUGE-1"])
    print("ROUGE-2:", metrics["ROUGE-2"])
    print("ROUGE-L:", metrics["ROUGE-L"])


