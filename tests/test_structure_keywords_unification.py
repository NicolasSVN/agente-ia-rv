"""Garante que worker (`UploadQueueService._STRUCTURE_KEYWORDS`) e endpoints
(`_STRUCTURE_KEYWORDS_AI` / `_STRUCTURE_KEYWORDS_CONFIRM`) consomem da mesma
fonte da verdade (`services.structure_keywords.STRUCTURE_KEYWORDS`).

Roda standalone: `python tests/test_structure_keywords_unification.py` ou via pytest.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.structure_keywords import STRUCTURE_KEYWORDS, find_structure_keyword
from services.upload_queue import UploadQueue as UploadQueueService


def test_worker_uses_canonical_list():
    assert UploadQueueService._STRUCTURE_KEYWORDS is STRUCTURE_KEYWORDS, (
        "Worker deve referenciar diretamente services.structure_keywords.STRUCTURE_KEYWORDS"
    )


def test_endpoints_use_canonical_list():
    # api/endpoints/products.py importa _STRUCTURE_KEYWORDS_AI e
    # _STRUCTURE_KEYWORDS_CONFIRM dentro do escopo das funções, então fazemos
    # uma checagem textual: os símbolos importados são apenas aliases para
    # STRUCTURE_KEYWORDS (não há mais tuplas literais nas duas funções).
    src = (ROOT / "api" / "endpoints" / "products.py").read_text(encoding="utf-8")
    # Não deve sobrar nenhuma tupla literal "_STRUCTURE_KEYWORDS_AI = (" ou
    # "_STRUCTURE_KEYWORDS_CONFIRM = (" no arquivo.
    assert not re.search(r"_STRUCTURE_KEYWORDS_AI\s*=\s*\(", src), (
        "_STRUCTURE_KEYWORDS_AI ainda definido como tupla literal em products.py"
    )
    assert not re.search(r"_STRUCTURE_KEYWORDS_CONFIRM\s*=\s*\(", src), (
        "_STRUCTURE_KEYWORDS_CONFIRM ainda definido como tupla literal em products.py"
    )
    # Deve haver imports da fonte canônica
    assert "from services.structure_keywords import STRUCTURE_KEYWORDS as _STRUCTURE_KEYWORDS_AI" in src
    assert "from services.structure_keywords import STRUCTURE_KEYWORDS as _STRUCTURE_KEYWORDS_CONFIRM" in src


def test_canonical_covers_known_terms():
    """Todos os termos historicamente presentes em qualquer das listas devem
    estar na lista unificada."""
    expected = {
        # do worker
        "pop", "collar", "fence", "booster", "put spread", "call spread",
        "seagull", "worst of", "worst-of", "coe", "strangle", "straddle",
        "borboleta", "butterfly", "trava de alta", "trava de baixa",
        "operação estruturada", "produto estruturado", "nota estruturada",
        # exclusivos dos endpoints (estavam divergindo)
        "estruturada", "estruturado", "worst/of", "put/call spread",
        "reverse convertible", "knock-out", "knock out",
    }
    missing = expected - set(STRUCTURE_KEYWORDS)
    assert not missing, f"Keywords ausentes da lista canônica: {missing}"


def test_detection_is_consistent_between_worker_and_helper():
    """Worker._detect_structure_in_name e find_structure_keyword devem detectar
    o mesmo conjunto de termos para cada amostra."""
    samples = [
        "POP RAPT4 dez28.pdf",
        "Booster Vale dez25",
        "Seagull Petro abr26",
        "Reverse Convertible BBSE3",
        "Knock-out Itaú",
        "Análise da estrutura de capital da Vale",  # NÃO deve casar
        "Put Spread Magalu",
        "Worst Of Tech",
        "Nota estruturada XPTO",
        "Relatório trimestral de Itaú",  # NÃO deve casar
    ]
    for s in samples:
        worker_hit = UploadQueueService._detect_structure_in_name(s)
        helper_hit = find_structure_keyword(s)
        assert worker_hit == helper_hit, (
            f"Divergência em {s!r}: worker={worker_hit!r} helper={helper_hit!r}"
        )


def test_negative_no_false_positive_on_capital_structure():
    """Termo 'estrutura' isolado NÃO deve casar (apenas 'estruturada'/'estruturado')."""
    assert find_structure_keyword("Estrutura de capital da Vale") is None
    assert find_structure_keyword("estrutura a termo de juros") is None
    # mas a forma adjetivada casa
    assert find_structure_keyword("Nota estruturada XPTO") in ("estruturada", "nota estruturada")


if __name__ == "__main__":
    test_worker_uses_canonical_list()
    test_endpoints_use_canonical_list()
    test_canonical_covers_known_terms()
    test_detection_is_consistent_between_worker_and_helper()
    test_negative_no_false_positive_on_capital_structure()
    print("OK — todas as checagens passaram.")
