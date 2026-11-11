"""Import shim for environments where KenLM cannot be compiled.

Jiayan imports ``kenlm`` at package import time.  Its official
``WordNgramTokenizer`` does not use a language model; this shim lets that
tokenizer run while making any attempt to load a KenLM model fail loudly.
"""


class LanguageModel:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "KenLM is not available in this isolated environment; "
            "Jiayan CharHMMTokenizer/load_lm cannot be used."
        )
