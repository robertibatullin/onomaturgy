import pytest
from generators.name_transformers import (
    AdjectiveFromEthnonymGenerator,
    CountryNameFromLatinEthnonymGenerator,
    CountryNameFromNativeEthnonymGenerator,
    DynastyNameGenerator,
)


class TestAdjectiveFromEthnonymGenerator:
    def _gen(self, ethnonym):
        g = AdjectiveFromEthnonymGenerator(ethnonym)
        g.train()
        return g.generate(1)

    def test_ii_ending(self):
        # Germanii → German + ian
        assert 'Germanian' in self._gen('Germanii')

    def test_i_ending(self):
        assert 'Sclavian' in self._gen('Sclavi')

    def test_es_ending_produces_ian_and_ean(self):
        result = self._gen('Saxones')
        assert 'Saxonian' in result
        assert 'Saxonean' in result

    def test_ans_ending(self):
        assert 'Roman' in self._gen('Romans')

    def test_s_ending(self):
        assert 'Frankian' in self._gen('Franks')

    def test_ae_ending_produces_n_and_nian(self):
        result = self._gen('Baltae')
        assert 'Baltan' in result
        assert 'Baltanian' in result

    def test_vowel_ending(self):
        # ends in vowel → append 'nian'
        assert 'Galenian' in self._gen('Gale')

    def test_other_ending_unchanged(self):
        # consonant ending, no matching rule → returned as-is
        assert 'Bulgar' in self._gen('Bulgar')

    def test_train_sets_is_trained(self):
        g = AdjectiveFromEthnonymGenerator('Saxones')
        assert g.is_trained is False
        g.train()
        assert g.is_trained is True

    def test_equality_same_ethnonym(self):
        g1 = AdjectiveFromEthnonymGenerator('Saxones')
        g2 = AdjectiveFromEthnonymGenerator('Saxones')
        assert g1 == g2

    def test_inequality_different_ethnonym(self):
        assert (AdjectiveFromEthnonymGenerator('Saxones')
                != AdjectiveFromEthnonymGenerator('Franci'))


class TestCountryNameFromLatinEthnonymGenerator:
    def _gen(self, ethnonym):
        g = CountryNameFromLatinEthnonymGenerator(ethnonym)
        g.train()
        return g.generate(1)

    def test_ii_ending(self):
        assert 'Germania' in self._gen('Germanii')

    def test_i_ending(self):
        # Sclavi → Sclav + ia
        assert 'Sclavia' in self._gen('Sclavi')

    def test_es_ending(self):
        assert 'Saxonia' in self._gen('Saxones')

    def test_ians_ending(self):
        # endswith 'ians' → ethnonym[:-2] e.g. 'Persians'[:-2] = 'Persia'
        assert 'Persia' in self._gen('Persians')

    def test_ans_ending_two_forms(self):
        result = self._gen('Romans')
        # endswith 'ans': produces name[:-1] and name[:-2]
        assert 'Roman' in result or 'Roma' in result

    def test_s_ending_two_forms(self):
        result = self._gen('Francs')
        assert 'Francia' in result or 'Franc' in result

    def test_ae_ending_two_forms(self):
        # 'Baltae'[:-1] = 'Balta', 'Baltae'[:-1] + 'nia' = 'Baltania'
        result = self._gen('Baltae')
        assert 'Balta' in result and 'Baltania' in result

    def test_other_ending_two_forms(self):
        result = self._gen('Bulgar')
        assert 'Bulgar' in result or 'Bulgaria' in result

    def test_equality(self):
        g1 = CountryNameFromLatinEthnonymGenerator('Saxones')
        g2 = CountryNameFromLatinEthnonymGenerator('Saxones')
        assert g1 == g2

    def test_inequality(self):
        assert (CountryNameFromLatinEthnonymGenerator('Saxones')
                != CountryNameFromLatinEthnonymGenerator('Franci'))


class TestCountryNameFromNativeEthnonymGenerator:
    def _gen(self, ethnonym, family=None):
        g = CountryNameFromNativeEthnonymGenerator(ethnonym, language_family=family)
        g.train()
        return g.generate(1)

    def test_germanic_produces_land_form(self):
        assert 'Saxonland' in self._gen('Saxons', 'Germanic')

    def test_germanic_produces_en_form(self):
        assert 'Saxonen' in self._gen('Saxons', 'Germanic')

    def test_germanic_strips_trailing_s(self):
        result = self._gen('Franks', 'Germanic')
        assert 'Frankland' in result

    def test_celtic_produces_singular(self):
        result = self._gen('Gaels', 'Celtic')
        assert 'Gael' in result

    def test_celtic_produces_dal_form(self):
        result = self._gen('Gaels', 'Celtic')
        assert 'Dal Gael' in result

    def test_finnic_produces_maa_suffix(self):
        assert 'Suomimaa' in self._gen('Suomi', 'Finnic')

    def test_unknown_family_returns_empty(self):
        assert self._gen('Foo', None) == []

    def test_equality_same_args(self):
        g1 = CountryNameFromNativeEthnonymGenerator('Saxons', 'Germanic')
        g2 = CountryNameFromNativeEthnonymGenerator('Saxons', 'Germanic')
        assert g1 == g2

    def test_inequality_different_family(self):
        assert (CountryNameFromNativeEthnonymGenerator('Saxons', 'Germanic')
                != CountryNameFromNativeEthnonymGenerator('Saxons', 'Celtic'))


class TestDynastyNameGenerator:
    @pytest.mark.integration
    def test_old_norse_all_end_in_ing(self):
        g = DynastyNameGenerator('OldNorse', pattern=None, markov=0.0)
        g.train()
        result = g.generate(10)
        assert all(n.endswith('ing') for n in result)

    @pytest.mark.integration
    def test_old_german_all_end_in_ing(self):
        g = DynastyNameGenerator('OldGerman', pattern=None, markov=0.0)
        g.train()
        result = g.generate(10)
        assert all(n.endswith('ing') for n in result)

    @pytest.mark.integration
    def test_anglosaxon_all_end_in_ing(self):
        g = DynastyNameGenerator('AngloSaxon', pattern=None, markov=0.0)
        g.train()
        result = g.generate(10)
        assert all(n.endswith('ing') for n in result)

    @pytest.mark.integration
    def test_old_irish_all_start_with_ui(self):
        g = DynastyNameGenerator('OldIrish', pattern=None, markov=0.0)
        g.train()
        result = g.generate(10)
        assert all(n.startswith('Ui ') for n in result)

    @pytest.mark.integration
    def test_other_language_all_end_in_id(self):
        g = DynastyNameGenerator('Russian', pattern=None, markov=0.0)
        g.train()
        result = g.generate(10)
        assert all(n.endswith('id') for n in result)
