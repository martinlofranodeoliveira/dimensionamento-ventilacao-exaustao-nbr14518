"""Testes unitários para a CLI de dimensionamento da NBR 14518."""

from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ventilacao_nbr14518 import __version__
from ventilacao_nbr14518.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz = Path(__file__).resolve().parent.parent
        self.exemplo = str(self.raiz / "examples" / "restaurante_a_la_carte_pesado.json")

    def test_versao(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = main(["--versao"])
            self.assertEqual(code, 0)
            self.assertIn(__version__, mock_out.getvalue())

    def test_catalogo(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = main(["catalogo"])
            self.assertEqual(code, 0)
            out = mock_out.getvalue()
            self.assertIn("CATÁLOGO NORMATIVO", out)
            self.assertIn("Leve (Light Duty)", out)
            self.assertIn("Coifa de Parede", out)

    def test_gerar_exemplo_stdout(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = main(["gerar-exemplo"])
            self.assertEqual(code, 0)
            self.assertIn("nome_projeto", mock_out.getvalue())

    def test_gerar_exemplo_arquivo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "exemplo_gerado.json"
            code = main(["gerar-exemplo", "--saida", str(out_file)])
            self.assertEqual(code, 0)
            self.assertTrue(out_file.exists())
            self.assertIn("nome_projeto", out_file.read_text(encoding="utf-8"))

    def test_calcular_texto(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = main(["calcular", self.exemplo])
            self.assertEqual(code, 0)
            out = mock_out.getvalue()
            self.assertIn("LOFRANO TECNOLOGIA", out)
            self.assertIn("VAZÃO DE PROJETO COM MARGEM", out)

    def test_calcular_json(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = main(["calcular", self.exemplo, "--formato", "json"])
            self.assertEqual(code, 0)
            self.assertIn('"norma": "ABNT NBR 14518:2020"', mock_out.getvalue())

    def test_calcular_csv(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = main(["calcular", self.exemplo, "--formato", "csv"])
            self.assertEqual(code, 0)
            self.assertIn("Parametro;Valor;Unidade", mock_out.getvalue())

    def test_calcular_svg(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = main(["calcular", self.exemplo, "--formato", "svg"])
            self.assertEqual(code, 0)
            self.assertIn("<svg", mock_out.getvalue())

    def test_calcular_pacote_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_file = Path(tmpdir) / "pacote_cli.zip"
            with patch("sys.stdout", new_callable=io.StringIO):
                code = main(["calcular", self.exemplo, "--pacote-zip", str(zip_file)])
                self.assertEqual(code, 0)
                self.assertTrue(zip_file.exists())

    def test_calcular_arquivo_inexistente(self) -> None:
        with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
            code = main(["calcular", "arquivo_que_nao_existe.json"])
            self.assertEqual(code, 1)
            self.assertIn("não encontrado", mock_err.getvalue())


if __name__ == "__main__":
    unittest.main()
