"""Modelos imutáveis e estruturas de dados para a ABNT NBR 14518:2020.

Garantia de exatidão analítica: todos os atributos numéricos físicos
são mantidos exclusivamente como frações racionais (Fraction) ou inteiros.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class EquipamentoCoccao:
    """Equipamento instalado na linha de cocção sob a coifa."""
    nome: str
    severidade: str          # 'leve', 'medio', 'pesado', 'extra_pesado'
    potencia_kw: Fraction
    comprimento_m: Fraction
    largura_m: Fraction

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("O nome do equipamento não pode ser vazio.")
        if self.potencia_kw < 0:
            raise ValueError(f"Potência do equipamento '{self.nome}' não pode ser negativa.")
        if self.comprimento_m <= 0:
            raise ValueError(f"Comprimento do equipamento '{self.nome}' deve ser estritamente positivo.")
        if self.largura_m <= 0:
            raise ValueError(f"Largura do equipamento '{self.nome}' deve ser estritamente positiva.")


@dataclass(frozen=True)
class TrechoDuto:
    """Configuração da rede de dutos de exaustão de gordura."""
    comprimento_m: Fraction
    quantidade_curvas_90: int = 2
    quantidade_curvas_45: int = 0
    tem_damper_corta_fogo: bool = True
    tipo_descarga: str = "saida_chapeu_chines"  # ou 'descarga_direta_veneziana'

    def __post_init__(self) -> None:
        if self.comprimento_m <= 0:
            raise ValueError("O comprimento do duto deve ser maior que zero.")
        if self.quantidade_curvas_90 < 0:
            raise ValueError("A quantidade de curvas 90° não pode ser negativa.")
        if self.quantidade_curvas_45 < 0:
            raise ValueError("A quantidade de curvas 45° não pode ser negativa.")


@dataclass(frozen=True)
class FiltrosSistema:
    """Conjunto de filtragem de gordura e odores na coifa e duto."""
    tem_filtro_inercial: bool = True       # Chicana lavável metálica (obrigatório NBR 14518)
    tem_filtro_eletrostatico: bool = False  # Opcional para cozinhas com alta emissão
    tem_filtro_carvao_ativado: bool = False # Opcional para desodorização urbana


@dataclass(frozen=True)
class DimensoesDutoSugeridas:
    """Dimensões nominais padronizadas recomendadas para o duto."""
    diametro_circular_mm: int
    retangular_largura_mm: int
    retangular_altura_mm: int
    velocidade_circular_efetiva_m_s: Fraction
    velocidade_retangular_efetiva_m_s: Fraction


@dataclass(frozen=True)
class EntradaProjeto:
    """Entrada completa para dimensionamento do sistema de exaustão."""
    nome_projeto: str
    localizacao: str
    tipo_coifa: str                        # 'parede', 'ilha', 'canto', 'compensadora'
    altura_montagem_m: Fraction            # Distância entre bloco de cocção e face da coifa (ex: 1,0 m)
    projecao_manual_m: Optional[Fraction]  # Sobrescrita da projeção perimetral mínima
    equipamentos: Tuple[EquipamentoCoccao, ...]
    duto: TrechoDuto
    filtros: FiltrosSistema = FiltrosSistema()
    taxa_compensacao: Fraction = Fraction(85, 100)      # 85% padrão
    margem_seguranca: Fraction = Fraction(10, 100)      # 10% padrão

    def __post_init__(self) -> None:
        if not self.nome_projeto or not self.nome_projeto.strip():
            raise ValueError("O nome do projeto é obrigatório.")
        if self.altura_montagem_m <= 0:
            raise ValueError("A altura de montagem da coifa deve ser maior que zero.")
        if not self.equipamentos:
            raise ValueError("A lista de equipamentos de cocção não pode estar vazia.")
        if self.taxa_compensacao <= 0 or self.taxa_compensacao > 1:
            raise ValueError("A taxa de compensação de ar deve estar entre 0 (exclusivo) e 1 (100%).")
        if self.margem_seguranca < 0:
            raise ValueError("A margem de segurança não pode ser negativa.")


@dataclass(frozen=True)
class ResultadoCalculo:
    """Resultado analítico e determinístico do dimensionamento NBR 14518."""
    nome_projeto: str
    localizacao: str
    tipo_coifa: str
    severidade_dominante: str
    
    # Geometria do Bloco e da Coifa
    comprimento_bloco_m: Fraction
    largura_bloco_m: Fraction
    potencia_total_kw: Fraction
    projecao_coifa_m: Fraction
    comprimento_coifa_m: Fraction
    largura_coifa_m: Fraction
    area_face_coifa_m2: Fraction
    perimetro_aberto_m: Fraction
    altura_montagem_m: Fraction

    # Vazões calculadas pelos métodos normativos
    vazao_captura_m3_h: Fraction
    vazao_face_m3_h: Fraction
    vazao_potencia_m3_h: Fraction
    metodo_determinante: str
    vazao_base_m3_h: Fraction
    vazao_projeto_m3_h: Fraction
    vazao_projeto_m3_s: Fraction
    vazao_compensacao_m3_h: Fraction

    # Duto de Exaustão
    area_duto_requerida_m2: Fraction
    velocidade_duto_adotada_m_s: Fraction
    duto_sugerido: DimensoesDutoSugeridas

    # Balanço de Pressão Estática e Total (em Pa e mmca)
    perda_coifa_plenum_pa: Fraction
    perda_filtros_pa: Fraction
    perda_duto_distribuida_pa: Fraction
    perda_duto_singular_pa: Fraction
    pressao_estatica_total_pa: Fraction
    pressao_estatica_total_mmca: Fraction
    pressao_dinamica_pa: Fraction
    pressao_total_ventilador_pa: Fraction
    pressao_total_ventilador_mmca: Fraction

    # Motor do Exaustor Centrífugo
    potencia_eixo_kw: Fraction
    potencia_eixo_cv: Fraction
    potencia_motor_requerida_cv: Fraction
    motor_comercial_cv: Fraction

    # Recomendações e notas normativas
    recomendacoes: Tuple[str, ...]
