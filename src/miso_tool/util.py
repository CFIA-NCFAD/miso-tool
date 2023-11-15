NT_SUB = str.maketrans("acgtrymkswhbvdnxACGTRYMKSWHBVDNX", "tgcayrkmswdvbhnxTGCAYRKMSWDVBHNX")


def revcomp(s):
    """Reverse complement nucleotide sequence

    Args:
        s (str): nucleotide sequence

    Returns:
        str: reverse complement of `s` nucleotide sequence
    """
    return s.translate(NT_SUB)[::-1]
