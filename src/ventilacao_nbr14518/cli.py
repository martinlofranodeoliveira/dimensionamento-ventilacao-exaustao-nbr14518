"""Interface de Linha de Comando (CLI) para a ABNT NBR 14518:2020.

Comandos disponíveis:
  calcular       Dimensiona sistema de exaustão e ventilação a partir de arquivo JSON.
  catalogo       Lista severidades, tipologias de coifa e parâmetros normativos.
  gerar-exemplo  Emite modelo JSON de entrada para edição.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List

from ventilacao_nbr14518 import __version__
from ventilacao_nbr14518.calculator import calcular_sistema_exaustao
from ventilacao_nbr14518.codecs import carregar_entrada_json, serializar_resultado_json
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
from ventilacao_nbr14518.svg_generator import gerar_painel_svg


def _criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nbr14518",
        description="Dimensionamento analítico de sistemas de ventilação e exaustão para cozinhas profissionais conforme ABNT NBR 14518:2020.",
    )
    parser.add_argument(
        "--versao", "-v",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Exibe a versão do programa e encerra.",
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comando a ser executado")

    # Comando: calcular
    calc_parser = subparsers.add_parser("calcular", help="Dimensiona o sistema a partir de um arquivo JSON")
    calc_parser.add_argument("arquivo_entrada", type=str, help="Caminho do arquivo JSON com dados do projeto")
    calc_parser.add_argument(
        "--formato", "-f",
        choices=["texto", "json", "csv", "svg"],
        default="texto",
        help="Formato de saída dos resultados (padrão: texto)",
    )
    calc_parser.add_argument(
        "--saida", "-o",
        type=str,
        default=None,
        help="Caminho do arquivo de saída (se omitido, imprime na saída padrão)",
    )
    calc_parser.add_argument(
        "--pacote-zip",
        type=str,
        default=None,
        help="Gera pacote ZIP determinístico completo no caminho especificado",
    )

    # Comando: catalogo
    subparsers.add_parser("catalogo", help="Exibe catálogo normativo e tabelas de referência")

    # Comando: gerar-exemplo
    ex_parser = subparsers.add_parser("gerar-exemplo", help="Gera um modelo JSON de exemplo pronto para preenchimento")
    ex_parser.add_argument(
        "--saida", "-o",
        type=str,
        default=None,
        help="Caminho onde salvar o exemplo JSON (se omitido, imprime no terminal)",
    )

    return parser


def comando_catalogo() -> int:
    """Exibe o catálogo de parâmetros normativos da NBR 14518:2020."""
    print("=" * 80)
    print("    CATÁLOGO NORMATIVO - ABNT NBR 14518:2020 (COZINHAS PROFISSIONAIS)")
    print("=" * 80)
    print("\n1. CLASSIFICAÇÃO DE SEVERIDADE DOS EQUIPAMENTOS DE COCÇÃO:")
    for chave, sev in CLASSIFICACOES_SEVERIDADE.items():
        print(f"  • {sev.nome} ({chave}):")
        print(f"      {sev.descricao}")
        print(f"      Vazão linear mínima: {int(sev.vazao_especifica_linear_min_m3_h_m)} m³/(h·m)")
        print(f"      Vazão por potência:  {int(sev.vazao_especifica_potencia_m3_h_kw)} m³/(h·kW)")
        print(f"      Velocidade captura:  {float(sev.velocidade_captura_parede_m_s):.2f} m/s (parede) | {float(sev.velocidade_captura_ilha_m_s):.2f} m/s (ilha)")
        print(f"      Velocidade de face:  {float(sev.velocidade_face_parede_m_s):.2f} m/s (parede) | {float(sev.velocidade_face_ilha_m_s):.2f} m/s (ilha)")

    print("\n2. TIPOLOGIAS DE COIFA E PROJEÇÕES MÍNIMAS:")
    for chave, tipo in TIPOS_COIFA.items():
        print(f"  • {tipo.nome} ({chave}):")
        print(f"      {tipo.descricao}")
        print(f"      Projeção mínima sobre cocção: {float(tipo.projecao_minima_m * 1000):.0f} mm")

    print("\n3. CATÁLOGO DE MOTORES COMERCIAIS PADRONIZADOS (cv):")
    motores_str = ", ".join(f"{float(m):.2f} cv" for m in MOTORES_COMERCIAIS_CV)
    print(f"  {motores_str}")
    print("=" * 80)
    return 0


def comando_gerar_exemplo(saida_path: str | None) -> int:
    """Gera um arquivo JSON de exemplo com valores reais de projeto."""
    exemplo_json = """{
  "nome_projeto": "Restaurante Contemporâneo - Linha de Cocção Principal",
  "localizacao": "São Paulo - SP",
  "tipo_coifa": "parede",
  "altura_montagem_m": "1.00",
  "projecao_manual_m": "0.20",
  "taxa_compensacao": "0.85",
  "margem_seguranca": "0.10",
  "equipamentos": [
    {
      "nome": "Fogão Industrial 6 Bocas Aberto a Gás",
      "severidade": "medio",
      "potencia_kw": "36.00",
      "comprimento_m": "1.20",
      "largura_m": "0.85"
    },
    {
      "nome": "Chapa Bifeteira a Gás",
      "severidade": "medio",
      "potencia_kw": "18.00",
      "comprimento_m": "0.80",
      "largura_m": "0.85"
    },
    {
      "nome": "Charbroiler Pedra Vulcânica a Gás",
      "severidade": "pesado",
      "potencia_kw": "24.00",
      "comprimento_m": "0.80",
      "largura_m": "0.85"
    },
    {
      "nome": "Fritadeira Alta Recuperação a Gás 28L",
      "severidade": "pesado",
      "potencia_kw": "22.00",
      "comprimento_m": "0.40",
      "largura_m": "0.85"
    }
  ],
  "duto": {
    "comprimento_m": "12.00",
    "quantidade_curvas_90": 2,
    "quantidade_curvas_45": 1,
    "tem_damper_corta_fogo": true,
    "tipo_descarga": "saida_chapeu_chines"
  },
  "filtros": {
    "tem_filtro_inercial": true,
    "tem_filtro_eletrostatico": false,
    "tem_filtro_carvao_ativado": false
  }
}
"""
    if saida_path:
        p = Path(saida_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(exemplo_json, encoding="utf-8")
        print(f"Exemplo gravado com sucesso em '{p}'.")
    else:
        sys.stdout.write(exemplo_json)
    return 0


def comando_calcular(
    arquivo_entrada: str,
    formato: str,
    saida: str | None,
    pacote_zip: str | None,
) -> int:
    """Carrega dados, executa dimensionamento e gera saídas solicitadas."""
    p_in = Path(arquivo_entrada)
    if not p_in.exists():
        print(f"Erro: Arquivo de entrada '{arquivo_entrada}' não encontrado.", file=sys.stderr)
        return 1

    entrada_bytes = p_in.read_bytes()
    entrada = carregar_entrada_json(entrada_bytes)
    resultado = calcular_sistema_exaustao(entrada)

    # Geração do formato solicitado
    if formato == "json":
        conteudo_saida = serializar_resultado_json(resultado)
    elif formato == "csv":
        conteudo_saida = gerar_csv_seguro(resultado)
    elif formato == "svg":
        conteudo_saida = gerar_painel_svg(resultado)
    else:  # texto
        conteudo_saida = gerar_relatorio_texto(resultado)

    if saida:
        p_out = Path(saida)
        p_out.parent.mkdir(parents=True, exist_ok=True)
        p_out.write_text(conteudo_saida, encoding="utf-8")
    else:
        sys.stdout.write(conteudo_saida)

    # Pacote ZIP determinístico opcional
    if pacote_zip:
        svg_bytes = gerar_painel_svg(resultado).encode("utf-8")
        exportar_pacote_zip(
            resultado,
            pacote_zip,
            entrada_json_bytes=entrada_bytes,
            svg_bytes=svg_bytes,
        )
        print(f"[ZIP] Pacote determinístico gerado em '{pacote_zip}'", file=sys.stderr)

    return 0


def main(argv: List[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    if argv is None:
        argv = sys.argv[1:]

    # Normalizar comandos com hífen para sublinhado se aplicável
    norm_argv: List[str] = []
    for arg in argv:
        if arg in ("--versao", "-v"):
            print(f"nbr14518 {__version__}")
            return 0
        norm_argv.append(arg)

    parser = _criar_parser()
    if not norm_argv:
        parser.print_help()
        return 0

    args = parser.parse_args(norm_argv)

    if args.comando == "catalogo":
        return comando_catalogo()
    elif args.comando == "gerar-exemplo":
        return comando_gerar_exemplo(args.saida)
    elif args.comando == "calcular":
        return comando_calcular(
            arquivo_entrada=args.arquivo_entrada,
            formato=args.formato,
            saida=args.saida,
            pacote_zip=args.pacote_zip,
        )
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
