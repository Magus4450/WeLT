from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoImageProcessor
from trl import pack_dataset
from utf8_tokenizer.tokenizer import UTF8Tokenizer

from welt.processor import TextImageProcessor

dataset = load_dataset("Helsinki-NLP/opus-100", "en-he", split="train")

processor = TextImageProcessor(
    tokenizer=UTF8Tokenizer(),
    image_processor=AutoImageProcessor.from_pretrained("WinKawaks/vit-tiny-patch16-224", use_fast=True),
)

# Convert dataset to text
dataset = dataset.map(
    lambda batch: {"text": f"<en>\x0E{batch['translation']['en']}\x0F<he> {batch['translation']['he']}"},
    remove_columns=["translation"])
dataset = processor.pretokenize_dataset(dataset)

dataset = pack_dataset(dataset, seq_length=128)
dataset = dataset.with_transform(processor)

for _ in tqdm(dataset):
    pass
