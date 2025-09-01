import warnings

import torch

from image_latent_transformer.pretokenizer.control import ControlTokens


def add_self_attention_blocks(mask: torch.Tensor, words: list[str]) -> None:
    # Attention blocks (PrefixLM / MAS) are surrounded by <ShiftOut> and <ShiftIn> tokens (`\xOE` ... `\x0F`).
    shift_out_idx = None
    for i, word in enumerate(words):
        if word == ControlTokens.ShiftOut:
            if shift_out_idx is not None:
                warnings.warn(
                    "Shift Out (SO) detected after another Shift Out (SO) without Shift In (SI). "
                    "Nested shift blocks are not allowed.",
                    stacklevel=2)
            shift_out_idx = i
        if word == ControlTokens.ShiftIn:
            if shift_out_idx is None:
                warnings.warn(
                    "Shift In (SI) detected, without first seeing Shift Out (SO). "
                    "Skipping self-attention block.",
                    stacklevel=2)
            else:
                mask[0, shift_out_idx:shift_out_idx + i, shift_out_idx:shift_out_idx + i] = 1
                shift_out_idx = None

    if shift_out_idx is not None:
        warnings.warn(
            "Unclosed Shift Out (SO) block detected at end of sequence. "
            "Missing corresponding Shift In (SI).",
            stacklevel=2)


def get_attention_mask_for_packed_sequence(seq_lengths: list[int], words: list[str] = None) -> torch.Tensor:
    """
    Returns a 3D attention mask for a packed sequence. (1, seq_len, seq_len)
    The first dimension represents the head dimension, which is set to 1 for broadcasting.
    """
    total_length = sum(seq_lengths)

    mask = torch.zeros((1, total_length, total_length), dtype=torch.bool)

    current_position = 0
    for length in seq_lengths:
        tril = torch.tril(torch.ones((length, length), dtype=torch.bool))
        mask[0, current_position:current_position + length, current_position:current_position + length] = tril
        current_position += length

    if words is not None:
        add_self_attention_blocks(mask, words)

    return mask


def get_position_ids_for_packed_sequence(seq_lengths: list[int]) -> torch.Tensor:
    total_length = sum(seq_lengths)

    positions = torch.zeros(total_length, dtype=torch.long)

    current_position = 0
    for length in seq_lengths:
        positions[current_position:current_position + length] = torch.arange(length, dtype=torch.long)
        current_position += length

    return positions
