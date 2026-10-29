from medra.mining.base import Miner
from medra.mining.miner import TextMiner
from medra.mining.stub import StubMiner

MINERS: dict[str, type] = {"text": TextMiner, "stub": StubMiner}


def make_miner(name: str, session_id: str) -> Miner:
    return MINERS[name](session_id)


__all__ = ["Miner", "TextMiner", "StubMiner", "MINERS", "make_miner"]
