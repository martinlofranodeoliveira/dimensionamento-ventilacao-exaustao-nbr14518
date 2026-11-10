"""Motor de cálculo analítico e determinístico da ABNT NBR 14518:2020.

Implementa os três métodos de cálculo de vazão de exaustão, dimensionamento
geométrico de coifas e dutos de gordura, ar de compensação, balanço de pressões
e seleção de motores de exaustores centrífugos.
Todos os cálculos utilizam estritamente frações racionais (Fraction) e inteiros.
"""

from __future__ import annotations

from fractions import Fraction
import math
from typing import List, Tuple

from ventilacao_nbr14518.constants import (
    CLASSIFICACOES_SEVERIDADE,
    COEFICIENTES_SINGULARES_K,
    DENSIDADE_AR_PADRAO_KG_M3,
    KW_POR_CV,
    MARGEM_SEGURANCA_MOTOR,
    MOTORES_COMERCIAIS_CV,
    PA_POR_MMCA,
    PERDA_COIFA_PLENUM_PA,
    PERDA_DAMPER_CORTA_FOGO_PA,
    PERDA_DESCARGA_CHAPEU_PA,
    PERDA_FILTRO_CARVAO_ATIVADO_PA,
    PERDA_FILTRO_ELETROSTATICO_PA,
    PERDA_FILTRO_INERCIAL_CHICANA_PA,
    PERDA_UNITARIA_DUTO_PA_POR_M,
    RENDIMENTO_EXAUSTOR_PADRAO,
    TIPOS_COIFA,
    VELOCIDADE_DUTO_MINIMA_M_S,
    VELOCIDADE_DUTO_RECOMENDADA_M_S,
)
from ventilacao_nbr14518.models import (
    DimensoesDutoSugeridas,
    EntradaProjeto,
    EquipamentoCoccao,
    ResultadoCalculo,
)


def _raiz_quadrada_fracao(f: Fraction) -> Fraction:
    """Calcula a raiz quadrada exata de uma fração usando aproximação de ponto fixo inteiro."""
    if f < 0:
        raise ValueError("Não é possível calcular raiz quadrada de número negativo.")
    if f == 0:
        return Fraction(0, 1)
    # Escala inteira de precisão 10^6
    escala = 1000000
    num = f.numerator
    den = f.denominator
    # sqrt(num / den) = sqrt(num * den * escala^2) / (den * escala)
    val_int = math.isqrt(num * den * escala * escala)
    return Fraction(val_int, den * escala)


def determinar_severidade_dominante(equipamentos: Tuple[EquipamentoCoccao, ...]) -> str:
    """Determina a severidade dominante da linha de cocção."""
    prioridade = {"extra_pesado": 4, "pesado": 3, "medio": 2, "leve": 1}
    maior = "leve"
    maior_peso = 1
    for eq in equipamentos:
        peso = prioridade.get(eq.severidade, 1)
        if peso > maior_peso:
            maior_peso = peso
            maior = eq.severidade
    return maior


def calcular_dimensoes_duto_sugeridas(area_m2: Fraction, vazao_m3_s: Fraction) -> DimensoesDutoSugeridas:
    """Calcula dimensões comerciais nominais de duto circular e retangular."""
    # Diâmetro equivalente circular: D = sqrt(4 * A / pi), com pi ~ 355/113
    pi_frac = Fraction(355, 113)
    d_m = _raiz_quadrada_fracao((Fraction(4, 1) * area_m2) / pi_frac)
    d_mm_raw = int(d_m * 1000)
    # Arredondar para o múltiplo de 50 mm imediatamente superior (mínimo 200 mm)
    diametro_circular_mm = max(200, ((d_mm_raw + 49) // 50) * 50)
    
    # Área circular real
    d_m_real = Fraction(diametro_circular_mm, 1000)
    area_circ_real = (pi_frac * d_m_real * d_m_real) / Fraction(4, 1)
    v_circ_efetiva = vazao_m3_s / area_circ_real

    # Seção retangular: proporção ~ 4:3 ou próxima
    # H = sqrt(A / 1.333), W = 1.333 * H
    # Busca par (W, H) em múltiplos de 50 mm cuja área >= area_m2
    lado_base_mm = int(_raiz_quadrada_fracao(area_m2) * 1000)
    w_mm = max(250, ((lado_base_mm + 49) // 50) * 50)
    # Altura necessária para atingir a área
    w_m = Fraction(w_mm, 1000)
    h_m_raw = area_m2 / w_m
    h_mm_raw = int(h_m_raw * 1000)
    h_mm = max(200, ((h_mm_raw + 49) // 50) * 50)

    area_ret_real = Fraction(w_mm * h_mm, 1000000)
    v_ret_efetiva = vazao_m3_s / area_ret_real

    return DimensoesDutoSugeridas(
        diametro_circular_mm=diametro_circular_mm,
        retangular_largura_mm=w_mm,
        retangular_altura_mm=h_mm,
        velocidade_circular_efetiva_m_s=v_circ_efetiva,
        velocidade_retangular_efetiva_m_s=v_ret_efetiva,
    )


def calcular_sistema_exaustao(entrada: EntradaProjeto) -> ResultadoCalculo:
    """Executa o dimensionamento completo conforme a ABNT NBR 14518:2020."""
    if entrada.tipo_coifa not in TIPOS_COIFA:
        raise ValueError(f"Tipo de coifa inválido: '{entrada.tipo_coifa}'. Válidos: {list(TIPOS_COIFA.keys())}")

    tipo_info = TIPOS_COIFA[entrada.tipo_coifa]
    severidade = determinar_severidade_dominante(entrada.equipamentos)
    param_sev = CLASSIFICACOES_SEVERIDADE[severidade]

    # Geometria do bloco de cocção
    comprimento_bloco_m = sum(eq.comprimento_m for eq in entrada.equipamentos)
    largura_bloco_m = max(eq.largura_m for eq in entrada.equipamentos)
    potencia_total_kw = sum(eq.potencia_kw for eq in entrada.equipamentos)

    # Projeção da coifa sobre os limites do bloco
    projecao_coifa_m = tipo_info.projecao_minima_m
    if entrada.projecao_manual_m is not None:
        if entrada.projecao_manual_m < tipo_info.projecao_minima_m:
            # Garante que nunca seja menor que o mínimo normativo
            projecao_coifa_m = tipo_info.projecao_minima_m
        else:
            projecao_coifa_m = entrada.projecao_manual_m

    # Dimensões da coifa conforme tipologia
    if entrada.tipo_coifa in ("parede", "compensadora"):
        comprimento_coifa_m = comprimento_bloco_m + Fraction(2, 1) * projecao_coifa_m
        largura_coifa_m = largura_bloco_m + projecao_coifa_m
        perimetro_aberto_m = comprimento_coifa_m + Fraction(2, 1) * largura_coifa_m
    elif entrada.tipo_coifa == "ilha":
        comprimento_coifa_m = comprimento_bloco_m + Fraction(2, 1) * projecao_coifa_m
        largura_coifa_m = largura_bloco_m + Fraction(2, 1) * projecao_coifa_m
        perimetro_aberto_m = Fraction(2, 1) * (comprimento_coifa_m + largura_coifa_m)
    elif entrada.tipo_coifa == "canto":
        comprimento_coifa_m = comprimento_bloco_m + projecao_coifa_m
        largura_coifa_m = largura_bloco_m + projecao_coifa_m
        perimetro_aberto_m = comprimento_coifa_m + largura_coifa_m
    else:
        raise ValueError(f"Tipologia desconhecida: {entrada.tipo_coifa}")

    area_face_coifa_m2 = comprimento_coifa_m * largura_coifa_m

    # 1. Método da Velocidade de Captura no Perímetro Livre
    eh_ilha = entrada.tipo_coifa == "ilha"
    v_cap = param_sev.velocidade_captura_ilha_m_s if eh_ilha else param_sev.velocidade_captura_parede_m_s
    # Q_captura = P_aberto * H * V_cap * 3600
    vazao_captura_m3_h = perimetro_aberto_m * entrada.altura_montagem_m * v_cap * Fraction(3600, 1)

    # 2. Método da Velocidade de Face da Coifa
    v_face = param_sev.velocidade_face_ilha_m_s if eh_ilha else param_sev.velocidade_face_parede_m_s
    # Q_face = A_face * V_face * 3600
    vazao_face_m3_h = area_face_coifa_m2 * v_face * Fraction(3600, 1)

    # 3. Método da Potência Térmica Instalada
    vazao_potencia_m3_h = Fraction(0, 1)
    for eq in entrada.equipamentos:
        p_sev = CLASSIFICACOES_SEVERIDADE[eq.severidade]
        vazao_potencia_m3_h += eq.potencia_kw * p_sev.vazao_especifica_potencia_m3_h_kw

    # Método Determinante e Vazão Base
    vazoes = [
        ("captura", vazao_captura_m3_h),
        ("face", vazao_face_m3_h),
        ("potencia", vazao_potencia_m3_h),
    ]
    metodo_determinante, vazao_base_m3_h = max(vazoes, key=lambda x: x[1])

    # Vazão de Projeto (com Margem de Segurança)
    fator_margem = Fraction(1, 1) + entrada.margem_seguranca
    vazao_projeto_m3_h = vazao_base_m3_h * fator_margem
    vazao_projeto_m3_s = vazao_projeto_m3_h / Fraction(3600, 1)

    # Vazão de Compensação de Ar (Make-up Air)
    vazao_compensacao_m3_h = vazao_projeto_m3_h * entrada.taxa_compensacao

    # Dimensionamento do Duto de Gordura
    v_duto_adotada = VELOCIDADE_DUTO_RECOMENDADA_M_S  # 11 m/s
    area_duto_requerida_m2 = vazao_projeto_m3_s / v_duto_adotada
    duto_sugerido = calcular_dimensoes_duto_sugeridas(area_duto_requerida_m2, vazao_projeto_m3_s)

    # Balanço de Pressões do Sistema (Pa e mmca)
    perda_coifa_plenum_pa = PERDA_COIFA_PLENUM_PA

    # Filtros
    perda_filtros_pa = Fraction(0, 1)
    if entrada.filtros.tem_filtro_inercial:
        perda_filtros_pa += PERDA_FILTRO_INERCIAL_CHICANA_PA
    if entrada.filtros.tem_filtro_eletrostatico:
        perda_filtros_pa += PERDA_FILTRO_ELETROSTATICO_PA
    if entrada.filtros.tem_filtro_carvao_ativado:
        perda_filtros_pa += PERDA_FILTRO_CARVAO_ATIVADO_PA

    # Perda distribuída no duto
    perda_duto_distribuida_pa = entrada.duto.comprimento_m * PERDA_UNITARIA_DUTO_PA_POR_M

    # Perdas singulares
    k_90 = COEFICIENTES_SINGULARES_K["curva_90_raio_curto"]
    k_45 = COEFICIENTES_SINGULARES_K["curva_45"]
    k_descarga = COEFICIENTES_SINGULARES_K.get(entrada.duto.tipo_descarga, Fraction(50, 100))
    k_total = (
        Fraction(entrada.duto.quantidade_curvas_90, 1) * k_90
        + Fraction(entrada.duto.quantidade_curvas_45, 1) * k_45
        + k_descarga
    )
    # Delta P sing = K * (rho * V^2 / 2)
    pressao_dinamica_pa = (DENSIDADE_AR_PADRAO_KG_M3 * v_duto_adotada * v_duto_adotada) / Fraction(2, 1)
    perda_duto_singular_pa = k_total * pressao_dinamica_pa
    if entrada.duto.tem_damper_corta_fogo:
        perda_duto_singular_pa += PERDA_DAMPER_CORTA_FOGO_PA

    # Pressão Estática Total
    pressao_estatica_total_pa = (
        perda_coifa_plenum_pa
        + perda_filtros_pa
        + perda_duto_distribuida_pa
        + perda_duto_singular_pa
    )
    pressao_estatica_total_mmca = pressao_estatica_total_pa / PA_POR_MMCA

    # Pressão Total do Ventilador = Estática + Dinâmica
    pressao_total_ventilador_pa = pressao_estatica_total_pa + pressao_dinamica_pa
    pressao_total_ventilador_mmca = pressao_total_ventilador_pa / PA_POR_MMCA

    # Potência do Exaustor Centrífugo
    # P_eixo_kW = (Q_m3_s * DeltaP_total_Pa) / (1000 * eta)
    potencia_eixo_kw = (vazao_projeto_m3_s * pressao_total_ventilador_pa) / (Fraction(1000, 1) * RENDIMENTO_EXAUSTOR_PADRAO)
    potencia_eixo_cv = potencia_eixo_kw / KW_POR_CV
    potencia_motor_requerida_cv = potencia_eixo_cv * MARGEM_SEGURANCA_MOTOR

    # Seleção de Motor Comercial Padronizado
    motor_comercial_cv = MOTORES_COMERCIAIS_CV[-1]
    for m in MOTORES_COMERCIAIS_CV:
        if m >= potencia_motor_requerida_cv:
            motor_comercial_cv = m
            break

    # Recomendações e Diretrizes Normativas
    recomendacoes: List[str] = [
        f"Norma ABNT NBR 14518:2020 - Cozinha profissional com severidade '{param_sev.nome}'.",
        f"Vazão de projeto adotada: {int(vazao_projeto_m3_h)} m³/h (determinada pelo método '{metodo_determinante}').",
        f"Ar de compensação obrigatório: {int(vazao_compensacao_m3_h)} m³/h ({int(entrada.taxa_compensacao * 100)}% da exaustão) para evitar pressão negativa excessiva.",
        f"Duto de gordura em chapa de aço soldada estanque (mínimo 18 MSG/1,21 mm de espessura) com velocidade nominal de {int(v_duto_adotada)} m/s (faixa normativa 10-12,5 m/s).",
    ]
    if entrada.filtros.tem_filtro_inercial:
        recomendacoes.append("Filtros inerciais tipo chicana laváveis instalados com inclinação mínima de 45° e calha coletora de gordura.")
    if entrada.duto.tem_damper_corta_fogo:
        recomendacoes.append("Damper corta-fogo com elemento termofusível (acionamento a 140°C) em conformidade com o Corpo de Bombeiros.")
    if entrada.tipo_coifa == "compensadora":
        recomendacoes.append("Coifa compensadora com insuflamento perimetral de ar não tratado/filtrado a baixa velocidade (<= 2 m/s).")
    recomendacoes.append(f"Exaustor centrífugo com motor fora do fluxo de ar (gabinete/plenum) e motor elétrico comercial de {float(motor_comercial_cv):.2f} cv selecionado.")

    return ResultadoCalculo(
        nome_projeto=entrada.nome_projeto,
        localizacao=entrada.localizacao,
        tipo_coifa=entrada.tipo_coifa,
        severidade_dominante=severidade,
        comprimento_bloco_m=comprimento_bloco_m,
        largura_bloco_m=largura_bloco_m,
        potencia_total_kw=potencia_total_kw,
        projecao_coifa_m=projecao_coifa_m,
        comprimento_coifa_m=comprimento_coifa_m,
        largura_coifa_m=largura_coifa_m,
        area_face_coifa_m2=area_face_coifa_m2,
        perimetro_aberto_m=perimetro_aberto_m,
        altura_montagem_m=entrada.altura_montagem_m,
        vazao_captura_m3_h=vazao_captura_m3_h,
        vazao_face_m3_h=vazao_face_m3_h,
        vazao_potencia_m3_h=vazao_potencia_m3_h,
        metodo_determinante=metodo_determinante,
        vazao_base_m3_h=vazao_base_m3_h,
        vazao_projeto_m3_h=vazao_projeto_m3_h,
        vazao_projeto_m3_s=vazao_projeto_m3_s,
        vazao_compensacao_m3_h=vazao_compensacao_m3_h,
        area_duto_requerida_m2=area_duto_requerida_m2,
        velocidade_duto_adotada_m_s=v_duto_adotada,
        duto_sugerido=duto_sugerido,
        perda_coifa_plenum_pa=perda_coifa_plenum_pa,
        perda_filtros_pa=perda_filtros_pa,
        perda_duto_distribuida_pa=perda_duto_distribuida_pa,
        perda_duto_singular_pa=perda_duto_singular_pa,
        pressao_estatica_total_pa=pressao_estatica_total_pa,
        pressao_estatica_total_mmca=pressao_estatica_total_mmca,
        pressao_dinamica_pa=pressao_dinamica_pa,
        pressao_total_ventilador_pa=pressao_total_ventilador_pa,
        pressao_total_ventilador_mmca=pressao_total_ventilador_mmca,
        potencia_eixo_kw=potencia_eixo_kw,
        potencia_eixo_cv=potencia_eixo_cv,
        potencia_motor_requerida_cv=potencia_motor_requerida_cv,
        motor_comercial_cv=motor_comercial_cv,
        recomendacoes=tuple(recomendacoes),
    )
