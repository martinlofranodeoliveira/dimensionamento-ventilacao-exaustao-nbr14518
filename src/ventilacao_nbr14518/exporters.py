"""Exportadores de dados, relatórios e empacotamento determinístico.

Conformidade Lofrano Tecnologia:
1. Relatório técnico em texto plano formatado e legível em pt-BR.
2. Exportador CSV com sanitização estrita contra injeção de fórmulas (CWE-1236).
3. Criação de pacotes ZIP com garantia os.O_EXCL (sem sobrescrita acidental)
   e timestamp fixo (2026, 1, 1, 0, 0, 0) para reproducibilidade determinística.
"""

from __future__ import annotations

import csv
from fractions import Fraction
import io
import os
from pathlib import Path
from typing import Any, List
import zipfile

from ventilacao_nbr14518.codecs import resultado_para_dict, serializar_resultado_json
from ventilacao_nbr14518.models import ResultadoCalculo


def _fmt_frac(f: Fraction, casas: int = 2) -> str:
    """Formata fração para string decimal em padrão brasileiro com vírgula."""
    fator = 10**casas
    val = (f.numerator * fator) // f.denominator
    s = str(val).zfill(casas + 1)
    inteiro = s[:-casas] if casas > 0 else s
    dec = s[-casas:] if casas > 0 else ""
    return f"{inteiro},{dec}" if casas > 0 else inteiro


def _sanitizar_campo_csv(val: Any) -> str:
    """Sanitiza strings para prevenir injeção de fórmulas em planilhas (CWE-1236)."""
    s = str(val)
    if s.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{s}"
    return s


def gerar_relatorio_texto(r: ResultadoCalculo) -> str:
    """Gera relatório de engenharia mecânica em texto formatado pt-BR."""
    linhas: List[str] = [
        "=" * 80,
        "    LOFRANO TECNOLOGIA - ENGENHARIA MECÂNICA E VENTILAÇÃO INDUSTRIAL",
        "    DIMENSIONAMENTO DE EXAUSTÃO PARA COZINHAS PROFISSIONAIS - ABNT NBR 14518:2020",
        "=" * 80,
        f"Projeto: {r.nome_projeto}",
        f"Localização: {r.localizacao}",
        f"Tipologia da Coifa: {r.tipo_coifa.upper()}",
        f"Severidade Dominante da Cocção: {r.severidade_dominante.upper()}",
        "-" * 80,
        "1. GEOMETRIA DO BLOCO DE COCÇÃO E DA COIFA",
        f"  - Comprimento do Bloco de Cocção:    {_fmt_frac(r.comprimento_bloco_m, 2)} m",
        f"  - Largura do Bloco de Cocção:        {_fmt_frac(r.largura_bloco_m, 2)} m",
        f"  - Potência Térmica Total Instalada:  {_fmt_frac(r.potencia_total_kw, 2)} kW",
        f"  - Projeção Perimetral Adotada:       {_fmt_frac(r.projecao_coifa_m, 3)} m (mínimo normativo atendido)",
        f"  - Comprimento da Coifa:              {_fmt_frac(r.comprimento_coifa_m, 2)} m",
        f"  - Largura da Coifa:                  {_fmt_frac(r.largura_coifa_m, 2)} m",
        f"  - Área da Face da Coifa:             {_fmt_frac(r.area_face_coifa_m2, 2)} m²",
        f"  - Perímetro Aberto de Sucção:        {_fmt_frac(r.perimetro_aberto_m, 2)} m",
        f"  - Altura de Montagem da Coifa:       {_fmt_frac(r.altura_montagem_m, 2)} m",
        "-" * 80,
        "2. VAZÕES DE EXAUSTÃO SEGUNDO OS CRITÉRIOS DA ABNT NBR 14518",
        f"  a) Método Velocidade de Captura:     {_fmt_frac(r.vazao_captura_m3_h, 2)} m³/h",
        f"  b) Método Velocidade de Face:        {_fmt_frac(r.vazao_face_m3_h, 2)} m³/h",
        f"  c) Método Potência dos Equipamentos: {_fmt_frac(r.vazao_potencia_m3_h, 2)} m³/h",
        f"  * Método Determinante Normativo:     {r.metodo_determinante.upper()}",
        f"  * Vazão Base de Exaustão:            {_fmt_frac(r.vazao_base_m3_h, 2)} m³/h",
        f"  * VAZÃO DE PROJETO COM MARGEM:       {_fmt_frac(r.vazao_projeto_m3_h, 2)} m³/h ({_fmt_frac(r.vazao_projeto_m3_s, 3)} m³/s)",
        "-" * 80,
        "3. AR DE COMPENSAÇÃO (MAKE-UP AIR)",
        f"  * VAZÃO DE INSUFLAMENTO REQUERIDA:   {_fmt_frac(r.vazao_compensacao_m3_h, 2)} m³/h",
        "  * Finalidade: Manter pressão negativa controlada (~ -5 Pa) e evitar refluxo.",
        "-" * 80,
        "4. REDE DE DUTOS DE GORDURA",
        f"  - Área Requerida da Seção:           {_fmt_frac(r.area_duto_requerida_m2, 4)} m²",
        f"  - Velocidade Nominal de Projeto:     {_fmt_frac(r.velocidade_duto_adotada_m_s, 2)} m/s (faixa 10-12,5 m/s)",
        f"  - Diâmetro Circular Sugerido:        Ø {r.duto_sugerido.diametro_circular_mm} mm (Vel. efetiva = {_fmt_frac(r.duto_sugerido.velocidade_circular_efetiva_m_s, 2)} m/s)",
        f"  - Seção Retangular Recomendada:      {r.duto_sugerido.retangular_largura_mm} x {r.duto_sugerido.retangular_altura_mm} mm (Vel. efetiva = {_fmt_frac(r.duto_sugerido.velocidade_retangular_efetiva_m_s, 2)} m/s)",
        "-" * 80,
        "5. BALANÇO DE PRESSÕES E PERDAS DE CARGA",
        f"  - Perda na Coifa e Plenum:           {_fmt_frac(r.perda_coifa_plenum_pa, 2)} Pa",
        f"  - Perda nos Filtros de Gordura:      {_fmt_frac(r.perda_filtros_pa, 2)} Pa",
        f"  - Perda Distribuída no Duto:         {_fmt_frac(r.perda_duto_distribuida_pa, 2)} Pa",
        f"  - Perda Singular em Conexões:        {_fmt_frac(r.perda_duto_singular_pa, 2)} Pa",
        f"  - Pressão Estática Total:            {_fmt_frac(r.pressao_estatica_total_pa, 2)} Pa ({_fmt_frac(r.pressao_estatica_total_mmca, 2)} mmca)",
        f"  - Pressão Dinâmica do Ar:            {_fmt_frac(r.pressao_dinamica_pa, 2)} Pa",
        f"  - PRESSÃO TOTAL DO VENTILADOR:       {_fmt_frac(r.pressao_total_ventilador_pa, 2)} Pa ({_fmt_frac(r.pressao_total_ventilador_mmca, 2)} mmca)",
        "-" * 80,
        "6. DIMENSIONAMENTO DO EXAUSTOR CENTRÍFUGO E MOTOR ELÉTRICO",
        f"  - Potência Mecânica no Eixo:         {_fmt_frac(r.potencia_eixo_kw, 2)} kW ({_fmt_frac(r.potencia_eixo_cv, 2)} cv)",
        f"  - Potência com Margem Operacional:   {_fmt_frac(r.potencia_motor_requerida_cv, 2)} cv",
        f"  - MOTOR COMERCIAL PADRONIZADO:       {_fmt_frac(r.motor_comercial_cv, 2)} cv",
        "-" * 80,
        "7. RECOMENDAÇÕES TÉCNICAS E DIRETRIZES DA ABNT NBR 14518:2020",
    ]
    for rec in r.recomendacoes:
        linhas.append(f"  * {rec}")
    linhas.extend([
        "=" * 80,
        "Emitido via Lofrano Tecnologia - Conforme ABNT NBR 14518:2020",
        "=" * 80,
    ])
    return "\n".join(linhas) + "\n"


def gerar_csv_seguro(r: ResultadoCalculo) -> str:
    """Gera planilha CSV com separador ponto-e-vírgula e proteção contra injeção de fórmulas."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")

    writer.writerow([_sanitizar_campo_csv("Parametro"), _sanitizar_campo_csv("Valor"), _sanitizar_campo_csv("Unidade")])
    writer.writerow([_sanitizar_campo_csv("Nome do Projeto"), _sanitizar_campo_csv(r.nome_projeto), ""])
    writer.writerow([_sanitizar_campo_csv("Localizacao"), _sanitizar_campo_csv(r.localizacao), ""])
    writer.writerow([_sanitizar_campo_csv("Tipologia da Coifa"), _sanitizar_campo_csv(r.tipo_coifa), ""])
    writer.writerow([_sanitizar_campo_csv("Severidade Dominante"), _sanitizar_campo_csv(r.severidade_dominante), ""])

    writer.writerow([_sanitizar_campo_csv("Comprimento Bloco"), _sanitizar_campo_csv(_fmt_frac(r.comprimento_bloco_m)), "m"])
    writer.writerow([_sanitizar_campo_csv("Largura Bloco"), _sanitizar_campo_csv(_fmt_frac(r.largura_bloco_m)), "m"])
    writer.writerow([_sanitizar_campo_csv("Potencia Total Instalada"), _sanitizar_campo_csv(_fmt_frac(r.potencia_total_kw)), "kW"])
    writer.writerow([_sanitizar_campo_csv("Projecao Coifa"), _sanitizar_campo_csv(_fmt_frac(r.projecao_coifa_m)), "m"])
    writer.writerow([_sanitizar_campo_csv("Comprimento Coifa"), _sanitizar_campo_csv(_fmt_frac(r.comprimento_coifa_m)), "m"])
    writer.writerow([_sanitizar_campo_csv("Largura Coifa"), _sanitizar_campo_csv(_fmt_frac(r.largura_coifa_m)), "m"])
    writer.writerow([_sanitizar_campo_csv("Area Face Coifa"), _sanitizar_campo_csv(_fmt_frac(r.area_face_coifa_m2)), "m2"])
    writer.writerow([_sanitizar_campo_csv("Perimetro Aberto"), _sanitizar_campo_csv(_fmt_frac(r.perimetro_aberto_m)), "m"])
    writer.writerow([_sanitizar_campo_csv("Altura Montagem"), _sanitizar_campo_csv(_fmt_frac(r.altura_montagem_m)), "m"])

    writer.writerow([_sanitizar_campo_csv("Vazao Metodo Captura"), _sanitizar_campo_csv(_fmt_frac(r.vazao_captura_m3_h)), "m3/h"])
    writer.writerow([_sanitizar_campo_csv("Vazao Metodo Face"), _sanitizar_campo_csv(_fmt_frac(r.vazao_face_m3_h)), "m3/h"])
    writer.writerow([_sanitizar_campo_csv("Vazao Metodo Potencia"), _sanitizar_campo_csv(_fmt_frac(r.vazao_potencia_m3_h)), "m3/h"])
    writer.writerow([_sanitizar_campo_csv("Metodo Determinante"), _sanitizar_campo_csv(r.metodo_determinante), ""])
    writer.writerow([_sanitizar_campo_csv("Vazao Base"), _sanitizar_campo_csv(_fmt_frac(r.vazao_base_m3_h)), "m3/h"])
    writer.writerow([_sanitizar_campo_csv("Vazao de Projeto"), _sanitizar_campo_csv(_fmt_frac(r.vazao_projeto_m3_h)), "m3/h"])
    writer.writerow([_sanitizar_campo_csv("Vazao de Compensacao"), _sanitizar_campo_csv(_fmt_frac(r.vazao_compensacao_m3_h)), "m3/h"])

    writer.writerow([_sanitizar_campo_csv("Area Duto Requerida"), _sanitizar_campo_csv(_fmt_frac(r.area_duto_requerida_m2, 4)), "m2"])
    writer.writerow([_sanitizar_campo_csv("Velocidade Duto Adotada"), _sanitizar_campo_csv(_fmt_frac(r.velocidade_duto_adotada_m_s)), "m/s"])
    writer.writerow([_sanitizar_campo_csv("Duto Circular Sugerido"), _sanitizar_campo_csv(r.duto_sugerido.diametro_circular_mm), "mm"])
    writer.writerow([_sanitizar_campo_csv("Duto Retangular W"), _sanitizar_campo_csv(r.duto_sugerido.retangular_largura_mm), "mm"])
    writer.writerow([_sanitizar_campo_csv("Duto Retangular H"), _sanitizar_campo_csv(r.duto_sugerido.retangular_altura_mm), "mm"])

    writer.writerow([_sanitizar_campo_csv("Pressao Estatica Total"), _sanitizar_campo_csv(_fmt_frac(r.pressao_estatica_total_pa)), "Pa"])
    writer.writerow([_sanitizar_campo_csv("Pressao Total Ventilador"), _sanitizar_campo_csv(_fmt_frac(r.pressao_total_ventilador_pa)), "Pa"])
    writer.writerow([_sanitizar_campo_csv("Pressao Total mmca"), _sanitizar_campo_csv(_fmt_frac(r.pressao_total_ventilador_mmca)), "mmca"])

    writer.writerow([_sanitizar_campo_csv("Potencia Eixo"), _sanitizar_campo_csv(_fmt_frac(r.potencia_eixo_kw)), "kW"])
    writer.writerow([_sanitizar_campo_csv("Potencia Requerida Motor"), _sanitizar_campo_csv(_fmt_frac(r.potencia_motor_requerida_cv)), "cv"])
    writer.writerow([_sanitizar_campo_csv("Motor Comercial Selecionado"), _sanitizar_campo_csv(_fmt_frac(r.motor_comercial_cv)), "cv"])

    return output.getvalue()


def exportar_pacote_zip(
    r: ResultadoCalculo,
    caminho_zip: str | Path,
    entrada_json_bytes: bytes | None = None,
    svg_bytes: bytes | None = None,
) -> None:
    """Cria pacote ZIP determinístico com garantia O_EXCL e timestamp congelado."""
    caminho = Path(caminho_zip)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(caminho, flags, 0o644)
    except FileExistsError:
        raise FileExistsError(f"O arquivo ZIP de destino já existe e não será sobrescrito: {caminho}")

    timestamp_fixo = (2026, 1, 1, 0, 0, 0)
    relatorio_txt = gerar_relatorio_texto(r).encode("utf-8")
    dados_csv = gerar_csv_seguro(r).encode("utf-8")
    resultado_json = serializar_resultado_json(r).encode("utf-8")

    with os.fdopen(fd, "wb") as f_zip:
        with zipfile.ZipFile(f_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 1. relatorio.txt
            zi_rel = zipfile.ZipInfo("relatorio.txt", date_time=timestamp_fixo)
            zi_rel.external_attr = 0o644 << 16
            zf.writestr(zi_rel, relatorio_txt)

            # 2. dados.csv
            zi_csv = zipfile.ZipInfo("dados.csv", date_time=timestamp_fixo)
            zi_csv.external_attr = 0o644 << 16
            zf.writestr(zi_csv, dados_csv)

            # 3. resultado.json
            zi_json = zipfile.ZipInfo("resultado.json", date_time=timestamp_fixo)
            zi_json.external_attr = 0o644 << 16
            zf.writestr(zi_json, resultado_json)

            # 4. entrada.json (se fornecido)
            if entrada_json_bytes is not None:
                zi_in = zipfile.ZipInfo("entrada.json", date_time=timestamp_fixo)
                zi_in.external_attr = 0o644 << 16
                zf.writestr(zi_in, entrada_json_bytes)

            # 5. painel.svg (se fornecido)
            if svg_bytes is not None:
                zi_svg = zipfile.ZipInfo("painel.svg", date_time=timestamp_fixo)
                zi_svg.external_attr = 0o644 << 16
                zf.writestr(zi_svg, svg_bytes)
