"""Constantes, tabelas e parâmetros normativos da ABNT NBR 14518:2020.

Sistemas de ventilação para cozinhas profissionais.
Todos os coeficientes e parâmetros são definidos como frações exatas (Fraction)
e inteiros para banir completamente erros de ponto flutuante IEEE-754.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, Final, List, NamedTuple


class ParametrosSeveridade(NamedTuple):
    """Parâmetros térmicos e normativos para classificação de equipamentos."""
    chave: str
    nome: str
    descricao: str
    vazao_especifica_linear_min_m3_h_m: Fraction  # m³/(h·m)
    vazao_especifica_potencia_m3_h_kw: Fraction   # m³/(h·kW)
    velocidade_captura_parede_m_s: Fraction       # m/s
    velocidade_captura_ilha_m_s: Fraction         # m/s
    velocidade_face_parede_m_s: Fraction          # m/s
    velocidade_face_ilha_m_s: Fraction            # m/s


# Tabela 1 e Seção 5 da ABNT NBR 14518:2020 - Classificação de Severidade de Cocção
CLASSIFICACOES_SEVERIDADE: Final[Dict[str, ParametrosSeveridade]] = {
    "leve": ParametrosSeveridade(
        chave="leve",
        nome="Leve (Light Duty)",
        descricao="Fornos elétricos, banho-maria, estufas térmicas, cafeteiras industriais, marmiteiros",
        vazao_especifica_linear_min_m3_h_m=Fraction(1000, 1),
        vazao_especifica_potencia_m3_h_kw=Fraction(25, 1),
        velocidade_captura_parede_m_s=Fraction(25, 100),   # 0,25 m/s
        velocidade_captura_ilha_m_s=Fraction(35, 100),     # 0,35 m/s
        velocidade_face_parede_m_s=Fraction(25, 100),      # 0,25 m/s
        velocidade_face_ilha_m_s=Fraction(35, 100),        # 0,35 m/s
    ),
    "medio": ParametrosSeveridade(
        chave="medio",
        nome="Médio (Medium Duty)",
        descricao="Fogões industriais com queimadores abertos, chapas bifeteiras, fritadeiras até 15 kW, fornos combinados",
        vazao_especifica_linear_min_m3_h_m=Fraction(1600, 1),
        vazao_especifica_potencia_m3_h_kw=Fraction(35, 1),
        velocidade_captura_parede_m_s=Fraction(35, 100),   # 0,35 m/s
        velocidade_captura_ilha_m_s=Fraction(45, 100),     # 0,45 m/s
        velocidade_face_parede_m_s=Fraction(30, 100),      # 0,30 m/s
        velocidade_face_ilha_m_s=Fraction(40, 100),        # 0,40 m/s
    ),
    "pesado": ParametrosSeveridade(
        chave="pesado",
        nome="Pesado (Heavy Duty)",
        descricao="Charbroilers a gás, fritadeiras de alta recuperação contínua (>15 kW), grelhas industriais, fogões Wok",
        vazao_especifica_linear_min_m3_h_m=Fraction(2200, 1),
        vazao_especifica_potencia_m3_h_kw=Fraction(45, 1),
        velocidade_captura_parede_m_s=Fraction(45, 100),   # 0,45 m/s
        velocidade_captura_ilha_m_s=Fraction(55, 100),     # 0,55 m/s
        velocidade_face_parede_m_s=Fraction(40, 100),      # 0,40 m/s
        velocidade_face_ilha_m_s=Fraction(50, 100),        # 0,50 m/s
    ),
    "extra_pesado": ParametrosSeveridade(
        chave="extra_pesado",
        nome="Extra-pesado (Extra Heavy Duty)",
        descricao="Equipamentos a combustível sólido (carvão/lenha), churrasqueiras de espeto corrido, parrilhas, fornos de pizza a lenha",
        vazao_especifica_linear_min_m3_h_m=Fraction(3000, 1),
        vazao_especifica_potencia_m3_h_kw=Fraction(60, 1),
        velocidade_captura_parede_m_s=Fraction(60, 100),   # 0,60 m/s
        velocidade_captura_ilha_m_s=Fraction(70, 100),     # 0,70 m/s
        velocidade_face_parede_m_s=Fraction(50, 100),      # 0,50 m/s
        velocidade_face_ilha_m_s=Fraction(60, 100),        # 0,60 m/s
    ),
}


class TipoCoifaInfo(NamedTuple):
    """Metadados e fatores geométricos por tipologia de coifa."""
    chave: str
    nome: str
    descricao: str
    projecao_minima_m: Fraction  # projeção sobre lados livres (NBR 14518 prescreve min 150mm)


TIPOS_COIFA: Final[Dict[str, TipoCoifaInfo]] = {
    "parede": TipoCoifaInfo(
        chave="parede",
        nome="Coifa de Parede (Adossada)",
        descricao="Coifa fixada contra alvenaria com 3 lados abertos à circulação",
        projecao_minima_m=Fraction(150, 1000),  # 0,15 m
    ),
    "ilha": TipoCoifaInfo(
        chave="ilha",
        nome="Coifa Central (Ilha)",
        descricao="Coifa suspensa sobre bloco de cocção central com 4 lados abertos",
        projecao_minima_m=Fraction(200, 1000),  # 0,20 m
    ),
    "canto": TipoCoifaInfo(
        chave="canto",
        nome="Coifa de Canto",
        descricao="Coifa encostada em duas paredes perpendiculares com 2 lados abertos",
        projecao_minima_m=Fraction(150, 1000),  # 0,15 m
    ),
    "compensadora": TipoCoifaInfo(
        chave="compensadora",
        nome="Coifa Compensadora (Insuflamento Integrado)",
        descricao="Coifa de parede com cortina de ar perimetral para make-up air integrado",
        projecao_minima_m=Fraction(150, 1000),  # 0,15 m
    ),
}


# Parâmetros de duto de gordura segundo ABNT NBR 14518
VELOCIDADE_DUTO_MINIMA_M_S: Final[Fraction] = Fraction(10, 1)      # 10,0 m/s (evita precipitação)
VELOCIDADE_DUTO_RECOMENDADA_M_S: Final[Fraction] = Fraction(11, 1)  # 11,0 m/s
VELOCIDADE_DUTO_MAXIMA_M_S: Final[Fraction] = Fraction(13, 1)      # 13,0 m/s (acima disso há ruído excessivo)

# Ar de compensação (Make-up air) NBR 14518
TAXA_COMPENSACAO_PADRAO: Final[Fraction] = Fraction(85, 100)       # 85% do ar exaurido
VELOCIDADE_DUTO_COMPENSACAO_M_S: Final[Fraction] = Fraction(5, 1)  # 5,0 m/s
VELOCIDADE_DIFUSOR_COMPENSACAO_M_S: Final[Fraction] = Fraction(2, 1) # 2,0 m/s (não perturba pluma)

# Perdas de carga estática de referência (em Pa)
PERDA_COIFA_PLENUM_PA: Final[Fraction] = Fraction(60, 1)          # 60 Pa
PERDA_PLENUM_COIFA_PA: Final[Fraction] = PERDA_COIFA_PLENUM_PA
PERDA_FILTRO_INERCIAL_CHICANA_PA: Final[Fraction] = Fraction(140, 1) # 140 Pa
PERDA_FILTRO_ELETROSTATICO_PA: Final[Fraction] = Fraction(90, 1)  # 90 Pa (se presente)
PERDA_FILTRO_CARVAO_ATIVADO_PA: Final[Fraction] = Fraction(160, 1) # 160 Pa (se presente)
PERDA_DAMPER_CORTA_FOGO_PA: Final[Fraction] = Fraction(40, 1)     # 40 Pa
PERDA_DESCARGA_CHAPEU_PA: Final[Fraction] = Fraction(50, 1)       # 50 Pa

# Perda de carga unitária de referência em dutos de chapa soldada estanque (Pa/m a ~11 m/s)
PERDA_UNITARIA_DUTO_PA_POR_M: Final[Fraction] = Fraction(12, 1)   # 12 Pa/m

# Perda em conexões (coeficientes de perda de carga singular K)
COEFICIENTES_SINGULARES_K: Final[Dict[str, Fraction]] = {
    "curva_90_raio_longo": Fraction(25, 100),       # K = 0,25
    "curva_90_raio_curto": Fraction(45, 100),       # K = 0,45
    "curva_45": Fraction(15, 100),                  # K = 0,15
    "transicao_gradual": Fraction(15, 100),          # K = 0,15
    "saida_chapeu_chines": Fraction(50, 100),        # K = 0,50
    "descarga_direta_veneziana": Fraction(70, 100),  # K = 0,70
}

# Densidade do ar padrão (kg/m³)
DENSIDADE_AR_PADRAO_KG_M3: Final[Fraction] = Fraction(12, 10)     # 1,20 kg/m³

# Rendimento mecânico padrão do exaustor centrífugo com motor fora do fluxo
RENDIMENTO_EXAUSTOR_PADRAO: Final[Fraction] = Fraction(70, 100)    # 70%
MARGEM_SEGURANCA_MOTOR: Final[Fraction] = Fraction(115, 100)       # 15% de sobrecapacidade

# Conversão exata de kW para cv métrico: 1 cv = 735,49875 W
KW_POR_CV: Final[Fraction] = Fraction(73549875, 100000000)        # ~0,7355 kW/cv

# Catálogo de Motores Comerciais Padronizados (cv)
MOTORES_COMERCIAIS_CV: Final[List[Fraction]] = [
    Fraction(1, 2),    # 0.5 cv
    Fraction(3, 4),    # 0.75 cv
    Fraction(1, 1),    # 1.0 cv
    Fraction(3, 2),    # 1.5 cv
    Fraction(2, 1),    # 2.0 cv
    Fraction(3, 1),    # 3.0 cv
    Fraction(4, 1),    # 4.0 cv
    Fraction(5, 1),    # 5.0 cv
    Fraction(15, 2),   # 7.5 cv
    Fraction(10, 1),   # 10.0 cv
    Fraction(25, 2),   # 12.5 cv
    Fraction(15, 1),   # 15.0 cv
    Fraction(20, 1),   # 20.0 cv
    Fraction(25, 1),   # 25.0 cv
    Fraction(30, 1),   # 30.0 cv
]

# Conversão exata de Pa para mmca: 1 mmca = 9,80665 Pa
PA_POR_MMCA: Final[Fraction] = Fraction(980665, 100000)
