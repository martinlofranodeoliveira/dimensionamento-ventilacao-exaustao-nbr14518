#!/usr/bin/env python3
"""Gera o painel vetorial SVG de exemplo e a imagem PNG correspondente em 1440x900."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from ventilacao_nbr14518.calculator import calcular_sistema_exaustao
from ventilacao_nbr14518.codecs import carregar_entrada_json
from ventilacao_nbr14518.svg_generator import gerar_painel_svg


def main() -> int:
    raiz = Path(__file__).resolve().parent.parent
    exemplo_json = raiz / "examples" / "restaurante_a_la_carte_pesado.json"
    docs_dir = raiz / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    svg_saida = docs_dir / "painel_exemplo.svg"
    png_saida = docs_dir / "exemplo.png"

    entrada = carregar_entrada_json(exemplo_json.read_bytes())
    resultado = calcular_sistema_exaustao(entrada)
    conteudo_svg = gerar_painel_svg(resultado)
    svg_saida.write_text(conteudo_svg, encoding="utf-8")
    print(f"SVG gerado em: {svg_saida}")

    # Tentar renderização via Chrome headless
    cmd = [
        "google-chrome",
        "--headless=new",
        "--hide-scrollbars",
        "--window-size=1440,900",
        f"--screenshot={png_saida}",
        str(svg_saida),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"PNG renderizado em: {png_saida} ({png_saida.stat().st_size} bytes)")
    except Exception as e:
        print(f"Aviso: Não foi possível renderizar PNG com google-chrome: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
