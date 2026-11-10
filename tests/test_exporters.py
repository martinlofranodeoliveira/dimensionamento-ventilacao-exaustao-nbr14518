"""Testes unitários para relatórios em texto, CSV sanitizado e ZIP determinístico."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
import zipfile

from ventilacao_nbr14518.calculator import calcular_sistema_exaustao
from ventilacao_nbr14518.exporters import (
    _sanitizar_campo_csv,
    exportar_pacote_zip,
    gerar_csv_seguro,
    gerar_relatorio_texto,
)
from ventilacao_nbr14518.models import EntradaProjeto, EquipamentoCoccao, TrechoDuto
from ventilacao_nbr14518.svg_generator import gerar_painel_svg


class TestExporters(unittest.TestCase):
    def setUp(self) -> None:
        eq = EquipamentoCoccao("Fogão Industrial", "pesado", Fraction(35, 1), Fraction(12, 10), Fraction(85, 100))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1))
        self.entrada = EntradaProjeto(
            nome_projeto="Projeto Exporters Test",
            localizacao="São Paulo",
            tipo_coifa="parede",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=Fraction(2, 10),
            equipamentos=(eq,),
            duto=duto,
        )
        self.resultado = calcular_sistema_exaustao(self.entrada)

    def test_gerar_relatorio_texto(self) -> None:
        rel = gerar_relatorio_texto(self.resultado)
        self.assertIn("LOFRANO TECNOLOGIA", rel)
        self.assertIn("ABNT NBR 14518:2020", rel)
        self.assertIn("1. GEOMETRIA DO BLOCO DE COCÇÃO", rel)
        self.assertIn("2. VAZÕES DE EXAUSTÃO", rel)
        self.assertIn("3. AR DE COMPENSAÇÃO (MAKE-UP AIR)", rel)
        self.assertIn("4. REDE DE DUTOS DE GORDURA", rel)
        self.assertIn("5. BALANÇO DE PRESSÕES", rel)
        self.assertIn("6. DIMENSIONAMENTO DO EXAUSTOR CENTRÍFUGO", rel)
        self.assertIn("7. RECOMENDAÇÕES TÉCNICAS", rel)

    def test_sanitizacao_csv(self) -> None:
        self.assertEqual(_sanitizar_campo_csv("Normal"), "Normal")
        self.assertEqual(_sanitizar_campo_csv("=SOMA(1;2)"), "'=SOMA(1;2)")
        self.assertEqual(_sanitizar_campo_csv("+123"), "'+123")
        self.assertEqual(_sanitizar_campo_csv("-10"), "'-10")
        self.assertEqual(_sanitizar_campo_csv("@cmd"), "'@cmd")
        self.assertEqual(_sanitizar_campo_csv("\ttab"), "'\ttab")

    def test_gerar_csv_seguro(self) -> None:
        csv_txt = gerar_csv_seguro(self.resultado)
        self.assertIn("Parametro;Valor;Unidade", csv_txt)
        self.assertIn("Nome do Projeto;Projeto Exporters Test;", csv_txt)
        self.assertIn("Vazao de Projeto;", csv_txt)
        self.assertIn("Motor Comercial Selecionado;", csv_txt)

    def test_gerar_painel_svg(self) -> None:
        svg = gerar_painel_svg(self.resultado)
        self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
        self.assertTrue(svg.strip().endswith("</svg>"))
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn("Projeto Exporters Test", svg)

    def test_exportar_pacote_zip_deterministico(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "teste_pacote.zip"
            exportar_pacote_zip(
                self.resultado,
                zip_path,
                entrada_json_bytes=b'{"teste": 1}',
                svg_bytes=b"<svg></svg>",
            )
            self.assertTrue(zip_path.exists())

            # Verificar membros do ZIP e timestamp congelado
            with zipfile.ZipFile(zip_path, "r") as zf:
                nomes = zf.namelist()
                self.assertIn("relatorio.txt", nomes)
                self.assertIn("dados.csv", nomes)
                self.assertIn("resultado.json", nomes)
                self.assertIn("entrada.json", nomes)
                self.assertIn("painel.svg", nomes)

                for info in zf.infolist():
                    self.assertEqual(info.date_time, (2026, 1, 1, 0, 0, 0))

            # Verificar que O_EXCL impede sobrescrita
            with self.assertRaises(FileExistsError):
                exportar_pacote_zip(self.resultado, zip_path)


if __name__ == "__main__":
    unittest.main()
