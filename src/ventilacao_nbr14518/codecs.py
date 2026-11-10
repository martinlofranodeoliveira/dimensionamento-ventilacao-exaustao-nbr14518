"""Codecs JSON estritos e canônicos conformes à RFC 8259.

Garantias de segurança e conformidade Lofrano Tecnologia:
1. Rejeição explícita de BOM (Byte Order Mark UTF-8 e UTF-16).
2. Banimento absoluto de floats IEEE-754: frações e decimais devem ser inteiros ou strings exatas.
3. Rejeição de chaves duplicadas em objetos JSON.
4. Limite de profundidade de aninhamento estrito (<= 32 níveis) para evitar estouro de pilha (DoS).
5. Serialização determinística e canônica (chaves ordenadas, separadores sem espaços inúteis).
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import json
from typing import Any, Dict, List, Tuple

from ventilacao_nbr14518.models import (
    DimensoesDutoSugeridas,
    EntradaProjeto,
    EquipamentoCoccao,
    FiltrosSistema,
    ResultadoCalculo,
    TrechoDuto,
)

PROFUNDIDADE_MAXIMA_PERMITIDA = 32


class ErroValidacaoCodec(ValueError):
    """Exceção levantada quando um JSON viola as regras estritas da RFC 8259 ou da Lofrano Tecnologia."""
    pass


def _par_chaves_unicas(pares: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """Constrói um dicionário rejeitando chaves duplicadas no JSON."""
    d: Dict[str, Any] = {}
    for chave, valor in pares:
        if chave in d:
            raise ErroValidacaoCodec(f"Chave duplicada detectada no objeto JSON: '{chave}'.")
        d[chave] = valor
    return d


def _rejeitar_float(valor_str: str) -> None:
    """Rejeita tokens de ponto flutuante no JSON de entrada."""
    raise ErroValidacaoCodec(
        f"Ponto flutuante nativo IEEE-754 '{valor_str}' detectado. "
        "A Lofrano Tecnologia exige que grandezas fracionárias sejam fornecidas como strings exatas ou inteiros."
    )


def _verificar_profundidade(obj: Any, nivel_atual: int = 0) -> None:
    """Verifica se a estrutura ultrapassa a profundidade máxima estipulada."""
    if nivel_atual > PROFUNDIDADE_MAXIMA_PERMITIDA:
        raise ErroValidacaoCodec(f"Profundidade de JSON ({nivel_atual}) excede o limite máximo permitido ({PROFUNDIDADE_MAXIMA_PERMITIDA}).")
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_profundidade(v, nivel_atual + 1)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_profundidade(item, nivel_atual + 1)


def _para_fracao(val: Any, campo: str) -> Fraction:
    """Converte com segurança valor inteiro, string ou decimal para Fraction exata."""
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        val_limpo = val.strip().replace(",", ".")
        if "/" in val_limpo:
            partes = val_limpo.split("/")
            if len(partes) == 2:
                try:
                    return Fraction(int(partes[0].strip()), int(partes[1].strip()))
                except (ValueError, ZeroDivisionError) as err:
                    raise ErroValidacaoCodec(f"Fração inválida no campo '{campo}': '{val}'.") from err
        try:
            d = Decimal(val_limpo)
            return Fraction(d)
        except Exception as err:
            raise ErroValidacaoCodec(f"Valor numérico inválido no campo '{campo}': '{val}'.") from err
    raise ErroValidacaoCodec(f"Tipo não permitido no campo '{campo}': {type(val).__name__}. Use string ou int.")


def carregar_entrada_json(conteudo: str | bytes) -> EntradaProjeto:
    """Decodifica e valida a entrada de dimensionamento a partir de JSON estrito."""
    if isinstance(conteudo, bytes):
        if conteudo.startswith(b"\xef\xbb\xbf"):
            raise ErroValidacaoCodec("Byte Order Mark (BOM) UTF-8 detectado e proibido.")
        if conteudo.startswith((b"\xff\xfe", b"\xfe\xff")):
            raise ErroValidacaoCodec("Byte Order Mark (BOM) UTF-16 detectado e proibido.")
        conteudo_str = conteudo.decode("utf-8")
    else:
        if conteudo.startswith("\ufeff"):
            raise ErroValidacaoCodec("Byte Order Mark (BOM) UTF-8 detectado e proibido.")
        conteudo_str = conteudo

    try:
        dados = json.loads(
            conteudo_str,
            object_pairs_hook=_par_chaves_unicas,
            parse_float=_rejeitar_float,
        )
    except json.JSONDecodeError as err:
        raise ErroValidacaoCodec(f"Erro de sintaxe JSON: {err}") from err

    _verificar_profundidade(dados)

    if not isinstance(dados, dict):
        raise ErroValidacaoCodec("O JSON raiz deve ser um objeto.")

    nome_projeto = dados.get("nome_projeto", "").strip()
    if not nome_projeto:
        raise ErroValidacaoCodec("O campo 'nome_projeto' é obrigatório.")

    localizacao = dados.get("localizacao", "Brasil").strip()
    tipo_coifa = dados.get("tipo_coifa", "parede").strip().lower()

    if "altura_montagem_m" not in dados:
        raise ErroValidacaoCodec("O campo 'altura_montagem_m' é obrigatório.")
    altura_montagem_m = _para_fracao(dados["altura_montagem_m"], "altura_montagem_m")

    projecao_manual_m = None
    if "projecao_manual_m" in dados and dados["projecao_manual_m"] is not None:
        projecao_manual_m = _para_fracao(dados["projecao_manual_m"], "projecao_manual_m")

    equipamentos_raw = dados.get("equipamentos")
    if not isinstance(equipamentos_raw, list) or not equipamentos_raw:
        raise ErroValidacaoCodec("O campo 'equipamentos' deve ser uma lista não vazia de equipamentos de cocção.")

    equipamentos: List[EquipamentoCoccao] = []
    for idx, eq in enumerate(equipamentos_raw):
        if not isinstance(eq, dict):
            raise ErroValidacaoCodec(f"O item #{idx + 1} em 'equipamentos' deve ser um objeto.")
        nome = eq.get("nome", "").strip()
        if not nome:
            raise ErroValidacaoCodec(f"O equipamento #{idx + 1} deve ter um 'nome'.")
        severidade = eq.get("severidade", "medio").strip().lower()
        if "potencia_kw" not in eq:
            raise ErroValidacaoCodec(f"O equipamento '{nome}' deve possuir o campo 'potencia_kw'.")
        if "comprimento_m" not in eq:
            raise ErroValidacaoCodec(f"O equipamento '{nome}' deve possuir o campo 'comprimento_m'.")
        if "largura_m" not in eq:
            raise ErroValidacaoCodec(f"O equipamento '{nome}' deve possuir o campo 'largura_m'.")

        potencia_kw = _para_fracao(eq["potencia_kw"], f"equipamentos[{idx}].potencia_kw")
        comprimento_m = _para_fracao(eq["comprimento_m"], f"equipamentos[{idx}].comprimento_m")
        largura_m = _para_fracao(eq["largura_m"], f"equipamentos[{idx}].largura_m")

        equipamentos.append(
            EquipamentoCoccao(
                nome=nome,
                severidade=severidade,
                potencia_kw=potencia_kw,
                comprimento_m=comprimento_m,
                largura_m=largura_m,
            )
        )

    duto_raw = dados.get("duto", {})
    if not isinstance(duto_raw, dict):
        raise ErroValidacaoCodec("O campo 'duto' deve ser um objeto.")
    if "comprimento_m" not in duto_raw:
        raise ErroValidacaoCodec("O campo 'duto.comprimento_m' é obrigatório.")
    comprimento_duto_m = _para_fracao(duto_raw["comprimento_m"], "duto.comprimento_m")
    qtd_90 = int(duto_raw.get("quantidade_curvas_90", 2))
    qtd_45 = int(duto_raw.get("quantidade_curvas_45", 0))
    tem_damper = bool(duto_raw.get("tem_damper_corta_fogo", True))
    tipo_descarga = duto_raw.get("tipo_descarga", "saida_chapeu_chines").strip().lower()

    duto = TrechoDuto(
        comprimento_m=comprimento_duto_m,
        quantidade_curvas_90=qtd_90,
        quantidade_curvas_45=qtd_45,
        tem_damper_corta_fogo=tem_damper,
        tipo_descarga=tipo_descarga,
    )

    filtros_raw = dados.get("filtros", {})
    filtros = FiltrosSistema(
        tem_filtro_inercial=bool(filtros_raw.get("tem_filtro_inercial", True)),
        tem_filtro_eletrostatico=bool(filtros_raw.get("tem_filtro_eletrostatico", False)),
        tem_filtro_carvao_ativado=bool(filtros_raw.get("tem_filtro_carvao_ativado", False)),
    )

    taxa_compensacao = Fraction(85, 100)
    if "taxa_compensacao" in dados:
        taxa_compensacao = _para_fracao(dados["taxa_compensacao"], "taxa_compensacao")

    margem_seguranca = Fraction(10, 100)
    if "margem_seguranca" in dados:
        margem_seguranca = _para_fracao(dados["margem_seguranca"], "margem_seguranca")

    return EntradaProjeto(
        nome_projeto=nome_projeto,
        localizacao=localizacao,
        tipo_coifa=tipo_coifa,
        altura_montagem_m=altura_montagem_m,
        projecao_manual_m=projecao_manual_m,
        equipamentos=tuple(equipamentos),
        duto=duto,
        filtros=filtros,
        taxa_compensacao=taxa_compensacao,
        margem_seguranca=margem_seguranca,
    )


def _fracao_para_decimal_str(f: Fraction, casas: int = 2) -> str:
    """Converte fração em representação decimal exata com número de casas definido."""
    fator = 10**casas
    val = (f.numerator * fator) // f.denominator
    s = str(val).zfill(casas + 1)
    inteiro = s[:-casas] if casas > 0 else s
    dec = s[-casas:] if casas > 0 else ""
    return f"{inteiro}.{dec}" if casas > 0 else inteiro


def resultado_para_dict(r: ResultadoCalculo) -> Dict[str, Any]:
    """Converte o resultado do cálculo em dicionário limpo para serialização canônica."""
    return {
        "norma": "ABNT NBR 14518:2020",
        "projeto": {
            "nome": r.nome_projeto,
            "localizacao": r.localizacao,
            "tipo_coifa": r.tipo_coifa,
            "severidade_dominante": r.severidade_dominante,
        },
        "geometria": {
            "bloco_comprimento_m": _fracao_para_decimal_str(r.comprimento_bloco_m, 2),
            "bloco_largura_m": _fracao_para_decimal_str(r.largura_bloco_m, 2),
            "potencia_total_kw": _fracao_para_decimal_str(r.potencia_total_kw, 2),
            "projecao_adotada_m": _fracao_para_decimal_str(r.projecao_coifa_m, 3),
            "coifa_comprimento_m": _fracao_para_decimal_str(r.comprimento_coifa_m, 2),
            "coifa_largura_m": _fracao_para_decimal_str(r.largura_coifa_m, 2),
            "coifa_area_face_m2": _fracao_para_decimal_str(r.area_face_coifa_m2, 2),
            "perimetro_aberto_m": _fracao_para_decimal_str(r.perimetro_aberto_m, 2),
            "altura_montagem_m": _fracao_para_decimal_str(r.altura_montagem_m, 2),
        },
        "vazoes": {
            "metodo_captura_m3_h": _fracao_para_decimal_str(r.vazao_captura_m3_h, 2),
            "metodo_face_m3_h": _fracao_para_decimal_str(r.vazao_face_m3_h, 2),
            "metodo_potencia_m3_h": _fracao_para_decimal_str(r.vazao_potencia_m3_h, 2),
            "metodo_determinante": r.metodo_determinante,
            "vazao_base_m3_h": _fracao_para_decimal_str(r.vazao_base_m3_h, 2),
            "vazao_projeto_m3_h": _fracao_para_decimal_str(r.vazao_projeto_m3_h, 2),
            "vazao_projeto_m3_s": _fracao_para_decimal_str(r.vazao_projeto_m3_s, 4),
            "vazao_compensacao_ar_m3_h": _fracao_para_decimal_str(r.vazao_compensacao_m3_h, 2),
        },
        "duto_gordura": {
            "area_requerida_m2": _fracao_para_decimal_str(r.area_duto_requerida_m2, 4),
            "velocidade_adotada_m_s": _fracao_para_decimal_str(r.velocidade_duto_adotada_m_s, 2),
            "sugestao_circular_mm": r.duto_sugerido.diametro_circular_mm,
            "sugestao_retangular_w_mm": r.duto_sugerido.retangular_largura_mm,
            "sugestao_retangular_h_mm": r.duto_sugerido.retangular_altura_mm,
            "velocidade_circular_efetiva_m_s": _fracao_para_decimal_str(r.duto_sugerido.velocidade_circular_efetiva_m_s, 2),
            "velocidade_retangular_efetiva_m_s": _fracao_para_decimal_str(r.duto_sugerido.velocidade_retangular_efetiva_m_s, 2),
        },
        "pressao_e_perdas": {
            "perda_coifa_plenum_pa": _fracao_para_decimal_str(r.perda_coifa_plenum_pa, 2),
            "perda_filtros_pa": _fracao_para_decimal_str(r.perda_filtros_pa, 2),
            "perda_duto_distribuida_pa": _fracao_para_decimal_str(r.perda_duto_distribuida_pa, 2),
            "perda_duto_singular_pa": _fracao_para_decimal_str(r.perda_duto_singular_pa, 2),
            "pressao_estatica_total_pa": _fracao_para_decimal_str(r.pressao_estatica_total_pa, 2),
            "pressao_estatica_total_mmca": _fracao_para_decimal_str(r.pressao_estatica_total_mmca, 2),
            "pressao_dinamica_pa": _fracao_para_decimal_str(r.pressao_dinamica_pa, 2),
            "pressao_total_ventilador_pa": _fracao_para_decimal_str(r.pressao_total_ventilador_pa, 2),
            "pressao_total_ventilador_mmca": _fracao_para_decimal_str(r.pressao_total_ventilador_mmca, 2),
        },
        "exaustor_e_motor": {
            "potencia_eixo_kw": _fracao_para_decimal_str(r.potencia_eixo_kw, 2),
            "potencia_eixo_cv": _fracao_para_decimal_str(r.potencia_eixo_cv, 2),
            "potencia_motor_requerida_cv": _fracao_para_decimal_str(r.potencia_motor_requerida_cv, 2),
            "motor_comercial_selecionado_cv": _fracao_para_decimal_str(r.motor_comercial_cv, 2),
        },
        "recomendacoes": list(r.recomendacoes),
    }


def serializar_resultado_json(r: ResultadoCalculo, indent: int | None = 2) -> str:
    """Serializa o resultado em JSON canônico RFC 8259."""
    d = resultado_para_dict(r)
    return json.dumps(d, ensure_ascii=False, indent=indent, sort_keys=True)
