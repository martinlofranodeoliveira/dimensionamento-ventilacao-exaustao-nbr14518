"""Dimensionamento de Sistemas de Ventilação e Exaustão para Cozinhas Profissionais - ABNT NBR 14518:2020.

Pacote de engenharia mecânica da Lofrano Tecnologia.
Aritmética 100% analítica e racional com fractions.Fraction (zero ponto flutuante).
"""

from __future__ import annotations

from ventilacao_nbr14518.calculator import (
    calcular_dimensoes_duto_sugeridas,
    calcular_sistema_exaustao,
    determinar_severidade_dominante,
)
from ventilacao_nbr14518.codecs import (
    carregar_entrada_json,
    resultado_para_dict,
    serializar_resultado_json,
)
from ventilacao_nbr14518.constants import (
    CLASSIFICACOES_SEVERIDADE,
    MOTORES_COMERCIAIS_CV,
    TIPOS_COIFA,
)
from ventilacao_nbr14518.exporters import (
    exportar_pacote_zip,
    gerar_csv_seguro,
    gerar_relatorio_texto,
)
from ventilacao_nbr14518.models import (
    DimensoesDutoSugeridas,
    EntradaProjeto,
    EquipamentoCoccao,
    FiltrosSistema,
    ResultadoCalculo,
    TrechoDuto,
)
from ventilacao_nbr14518.svg_generator import gerar_painel_svg

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "CLASSIFICACOES_SEVERIDADE",
    "TIPOS_COIFA",
    "MOTORES_COMERCIAIS_CV",
    "EquipamentoCoccao",
    "TrechoDuto",
    "FiltrosSistema",
    "DimensoesDutoSugeridas",
    "EntradaProjeto",
    "ResultadoCalculo",
    "determinar_severidade_dominante",
    "calcular_dimensoes_duto_sugeridas",
    "calcular_sistema_exaustao",
    "carregar_entrada_json",
    "resultado_para_dict",
    "serializar_resultado_json",
    "gerar_relatorio_texto",
    "gerar_csv_seguro",
    "exportar_pacote_zip",
    "gerar_painel_svg",
]
