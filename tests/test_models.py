"""Testes unitários para validação de modelos de dados da NBR 14518."""

from __future__ import annotations

from fractions import Fraction
import unittest

from ventilacao_nbr14518.models import (
    EntradaProjeto,
    EquipamentoCoccao,
    FiltrosSistema,
    TrechoDuto,
)


class TestModelos(unittest.TestCase):
    def test_equipamento_valido(self) -> None:
        eq = EquipamentoCoccao(
            nome="Fogão Industrial",
            severidade="medio",
            potencia_kw=Fraction(36, 1),
            comprimento_m=Fraction(12, 10),
            largura_m=Fraction(85, 100),
        )
        self.assertEqual(eq.nome, "Fogão Industrial")
        self.assertEqual(eq.severidade, "medio")
        self.assertEqual(eq.potencia_kw, Fraction(36, 1))

    def test_equipamento_invalido_nome_vazio(self) -> None:
        with self.assertRaises(ValueError):
            EquipamentoCoccao(
                nome="   ",
                severidade="medio",
                potencia_kw=Fraction(10, 1),
                comprimento_m=Fraction(1, 1),
                largura_m=Fraction(1, 1),
            )

    def test_equipamento_invalido_potencia_negativa(self) -> None:
        with self.assertRaises(ValueError):
            EquipamentoCoccao(
                nome="Chapa",
                severidade="medio",
                potencia_kw=Fraction(-5, 1),
                comprimento_m=Fraction(1, 1),
                largura_m=Fraction(1, 1),
            )

    def test_equipamento_invalido_dimensao_zero_ou_negativa(self) -> None:
        with self.assertRaises(ValueError):
            EquipamentoCoccao(
                nome="Chapa",
                severidade="medio",
                potencia_kw=Fraction(10, 1),
                comprimento_m=Fraction(0, 1),
                largura_m=Fraction(1, 1),
            )
        with self.assertRaises(ValueError):
            EquipamentoCoccao(
                nome="Chapa",
                severidade="medio",
                potencia_kw=Fraction(10, 1),
                comprimento_m=Fraction(1, 1),
                largura_m=Fraction(-1, 1),
            )

    def test_trecho_duto_valido(self) -> None:
        duto = TrechoDuto(
            comprimento_m=Fraction(15, 1),
            quantidade_curvas_90=2,
            quantidade_curvas_45=1,
            tem_damper_corta_fogo=True,
        )
        self.assertEqual(duto.comprimento_m, Fraction(15, 1))
        self.assertEqual(duto.quantidade_curvas_90, 2)

    def test_trecho_duto_invalido(self) -> None:
        with self.assertRaises(ValueError):
            TrechoDuto(comprimento_m=Fraction(0, 1))
        with self.assertRaises(ValueError):
            TrechoDuto(comprimento_m=Fraction(10, 1), quantidade_curvas_90=-1)
        with self.assertRaises(ValueError):
            TrechoDuto(comprimento_m=Fraction(10, 1), quantidade_curvas_45=-2)

    def test_entrada_projeto_valida(self) -> None:
        eq = EquipamentoCoccao("Fogão", "medio", Fraction(20, 1), Fraction(1, 1), Fraction(1, 1))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1))
        entrada = EntradaProjeto(
            nome_projeto="Projeto Cozinha",
            localizacao="SP",
            tipo_coifa="parede",
            altura_montagem_m=Fraction(1, 1),
            projecao_manual_m=None,
            equipamentos=(eq,),
            duto=duto,
        )
        self.assertEqual(entrada.nome_projeto, "Projeto Cozinha")
        self.assertEqual(entrada.taxa_compensacao, Fraction(85, 100))
        self.assertEqual(entrada.margem_seguranca, Fraction(10, 100))

    def test_entrada_projeto_invalidos(self) -> None:
        eq = EquipamentoCoccao("Fogão", "medio", Fraction(20, 1), Fraction(1, 1), Fraction(1, 1))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1))
        with self.assertRaises(ValueError):
            EntradaProjeto("", "SP", "parede", Fraction(1, 1), None, (eq,), duto)
        with self.assertRaises(ValueError):
            EntradaProjeto("P", "SP", "parede", Fraction(0, 1), None, (eq,), duto)
        with self.assertRaises(ValueError):
            EntradaProjeto("P", "SP", "parede", Fraction(1, 1), None, (), duto)
        with self.assertRaises(ValueError):
            EntradaProjeto("P", "SP", "parede", Fraction(1, 1), None, (eq,), duto, taxa_compensacao=Fraction(0, 1))
        with self.assertRaises(ValueError):
            EntradaProjeto("P", "SP", "parede", Fraction(1, 1), None, (eq,), duto, taxa_compensacao=Fraction(12, 10))
        with self.assertRaises(ValueError):
            EntradaProjeto("P", "SP", "parede", Fraction(1, 1), None, (eq,), duto, margem_seguranca=Fraction(-1, 10))


if __name__ == "__main__":
    unittest.main()
