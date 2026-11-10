"""Testes unitários para codecs JSON estritos RFC 8259."""

from __future__ import annotations

from fractions import Fraction
import unittest

from ventilacao_nbr14518.calculator import calcular_sistema_exaustao
from ventilacao_nbr14518.codecs import (
    ErroValidacaoCodec,
    carregar_entrada_json,
    resultado_para_dict,
    serializar_resultado_json,
)
from ventilacao_nbr14518.models import EntradaProjeto, EquipamentoCoccao, TrechoDuto


class TestCodecs(unittest.TestCase):
    def test_json_valido(self) -> None:
        json_txt = """{
            "nome_projeto": "Restaurante Teste",
            "localizacao": "Curitiba",
            "tipo_coifa": "parede",
            "altura_montagem_m": "1.00",
            "projecao_manual_m": "0.20",
            "taxa_compensacao": "0.85",
            "margem_seguranca": "0.10",
            "equipamentos": [
                {
                    "nome": "Fogão",
                    "severidade": "medio",
                    "potencia_kw": "30.00",
                    "comprimento_m": "1.00",
                    "largura_m": "0.80"
                }
            ],
            "duto": {
                "comprimento_m": "10.00",
                "quantidade_curvas_90": 2,
                "quantidade_curvas_45": 0,
                "tem_damper_corta_fogo": true,
                "tipo_descarga": "saida_chapeu_chines"
            }
        }"""
        entrada = carregar_entrada_json(json_txt)
        self.assertEqual(entrada.nome_projeto, "Restaurante Teste")
        self.assertEqual(entrada.altura_montagem_m, Fraction(1, 1))
        self.assertEqual(len(entrada.equipamentos), 1)

    def test_rejeicao_float_nativo(self) -> None:
        # Ponto flutuante sem aspas: 1.00 em vez de "1.00"
        json_com_float = """{
            "nome_projeto": "Teste",
            "tipo_coifa": "parede",
            "altura_montagem_m": 1.05,
            "equipamentos": [
                {
                    "nome": "Fogão",
                    "severidade": "medio",
                    "potencia_kw": "20.00",
                    "comprimento_m": "1.00",
                    "largura_m": "0.80"
                }
            ],
            "duto": { "comprimento_m": "10.00" }
        }"""
        with self.assertRaises(ErroValidacaoCodec):
            carregar_entrada_json(json_com_float)

    def test_rejeicao_bom_utf8_e_utf16(self) -> None:
        bom_utf8 = b"\xef\xbb\xbf" + b'{"nome_projeto": "Teste"}'
        with self.assertRaises(ErroValidacaoCodec):
            carregar_entrada_json(bom_utf8)

        bom_str = "\ufeff" + '{"nome_projeto": "Teste"}'
        with self.assertRaises(ErroValidacaoCodec):
            carregar_entrada_json(bom_str)

    def test_rejeicao_chaves_duplicadas(self) -> None:
        json_dup = """{
            "nome_projeto": "Teste 1",
            "nome_projeto": "Teste 2",
            "tipo_coifa": "parede",
            "altura_montagem_m": "1.00",
            "equipamentos": [],
            "duto": { "comprimento_m": "10.00" }
        }"""
        with self.assertRaises(ErroValidacaoCodec):
            carregar_entrada_json(json_dup)

    def test_rejeicao_profundidade_excessiva(self) -> None:
        # Aninhamento profundo > 32 níveis
        raiz: dict = {}
        curr = raiz
        for _ in range(35):
            curr["filho"] = {}
            curr = curr["filho"]
        import json
        profundo_str = json.dumps(raiz)
        with self.assertRaises(ErroValidacaoCodec):
            carregar_entrada_json(profundo_str)

    def test_serializacao_canonica(self) -> None:
        eq = EquipamentoCoccao("Fogão", "medio", Fraction(20, 1), Fraction(1, 1), Fraction(1, 1))
        duto = TrechoDuto(comprimento_m=Fraction(10, 1))
        entrada = EntradaProjeto("P", "SP", "parede", Fraction(1, 1), None, (eq,), duto)
        res = calcular_sistema_exaustao(entrada)

        json_out = serializar_resultado_json(res)
        self.assertIn("ABNT NBR 14518:2020", json_out)
        self.assertIn("vazoes", json_out)
        self.assertIn("duto_gordura", json_out)
        self.assertIn("pressao_e_perdas", json_out)
        self.assertIn("exaustor_e_motor", json_out)


    def test_parses_fracao_strings_variadas(self) -> None:
        json_txt = """{
            "nome_projeto": "Teste Formatos",
            "tipo_coifa": "parede",
            "altura_montagem_m": "1,05",
            "projecao_manual_m": "15/100",
            "taxa_compensacao": "85/100",
            "equipamentos": [
                {
                    "nome": "Equipamento 1",
                    "severidade": "leve",
                    "potencia_kw": 15,
                    "comprimento_m": "1.20",
                    "largura_m": "0,80"
                }
            ],
            "duto": { "comprimento_m": 12 }
        }"""
        ent = carregar_entrada_json(json_txt)
        self.assertEqual(ent.altura_montagem_m, Fraction(105, 100))
        self.assertEqual(ent.projecao_manual_m, Fraction(15, 100))
        self.assertEqual(ent.taxa_compensacao, Fraction(85, 100))
        self.assertEqual(ent.equipamentos[0].potencia_kw, Fraction(15, 1))
        self.assertEqual(ent.equipamentos[0].comprimento_m, Fraction(12, 10))
        self.assertEqual(ent.equipamentos[0].largura_m, Fraction(8, 10))
        self.assertEqual(ent.duto.comprimento_m, Fraction(12, 1))

    def test_fracao_invalida_lanca_erro(self) -> None:
        json_invalido = """{
            "nome_projeto": "Teste",
            "tipo_coifa": "parede",
            "altura_montagem_m": "divisao_por_zero/0",
            "equipamentos": [],
            "duto": { "comprimento_m": "10" }
        }"""
        with self.assertRaises(ErroValidacaoCodec):
            carregar_entrada_json(json_invalido)


if __name__ == "__main__":
    unittest.main()
