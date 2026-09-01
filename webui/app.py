"""Flask web UI for the onomaturgy name generators."""

import sys
import os

# Ensure the project root is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify

from onomaturgy import (
    SimpleNameGenerator,
    PersonalNameGenerator,
    PlaceNameGenerator,
    CompanyNameGenerator,
    TribalNameGenerator,
)

app = Flask(__name__)

PERSONAL_NAME_LANGUAGES = [
    'Abkhazian', 'Afghan', 'Albanian', 'AngloSaxon', 'Arabic', 'Armenian',
    'Azeri', 'Burmese', 'Cameroonian', 'Chinese', 'Czech', 'Danish', 'Dutch',
    'EarlyByzantine', 'English', 'Estonian', 'Ethiopian', 'Faeroese', 'Finnish',
    'French', 'Georgian', 'German', 'Gothic', 'Greek', 'Hungarian', 'Icelandic',
    'Indian', 'Indonesian', 'Iranian', 'Irish', 'Israeli', 'Italian', 'Japanese',
    'Kazakh', 'Khmer', 'Korean', 'Laotian', 'Latvian', 'Lithuanian', 'Malay',
    'Maltese', 'Norwegian', 'OldGerman', 'OldIrish', 'OldNorse', 'OldWelsh',
    'Pannonian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'SerboCroatian',
    'Spanish', 'Swedish', 'Thai', 'Turkish', 'Uzbek', 'Vietnamese',
]

TOPONYM_LANGUAGES = [
    'Abkhazian', 'Armenian', 'Azerbaijani', 'Basque', 'Catalan', 'Croatian',
    'Czech', 'Danish', 'Dutch', 'English', 'Estonian', 'Finnish', 'French',
    'Georgian', 'German', 'Icelandic', 'Irish', 'Italian', 'Latvian', 'Lithuanian',
    'NorthEastcaucasian', 'Norwegian', 'Ossetian', 'Polish', 'RomanWest', 'Scottish',
    'Spanish', 'Swedish', 'Welsh',
]

COMPANY_LANGUAGES = ['AL', 'AT', 'BA', 'CZ', 'DE', 'HR', 'HU', 'RO', 'RS', 'RU', 'SK', 'UA']

TRIBAL_LANGUAGES = ['Baltic', 'Celtic', 'Germanic', 'Slavic']

PLACE_CATEGORIES = [
    'area', 'basin', 'concave shoreline', 'convex shoreline', 'depression',
    'elevated area', 'elevation', 'island', 'marsh', 'populated place',
    'shoreline', 'strait', 'stream', 'underwater elevation',
]

INDUSTRIES = [
    'COMMUNICATIONS', 'CONSUMER DISCRETIONARY', 'CONSUMER STAPLES', 'ENERGY',
    'FINANCIALS', 'HEALTH CARE', 'INDUSTRIALS', 'INFORMATION TECHNOLOGY',
    'MATERIALS', 'REAL ESTATE', 'UTILITIES',
]

NAME_PARTS = ['given_name', 'patronymic', 'metronymic', 'surname']


@app.route('/')
def index():
    return render_template(
        'index.html',
        personal_name_languages=PERSONAL_NAME_LANGUAGES,
        toponym_languages=TOPONYM_LANGUAGES,
        company_languages=COMPANY_LANGUAGES,
        tribal_languages=TRIBAL_LANGUAGES,
        place_categories=PLACE_CATEGORIES,
        industries=INDUSTRIES,
        name_parts=NAME_PARTS,
    )


def _int_or_none(val):
    try:
        return int(val) if val not in ('', None) else None
    except (ValueError, TypeError):
        return None


def _collect_constraints(data, prefix=''):
    constraints = {}
    for key in ['max_characters', 'min_characters', 'max_syllables',
                'min_syllables', 'max_word_parts', 'min_word_parts']:
        v = _int_or_none(data.get(prefix + key))
        if v is not None:
            constraints[key] = v
    return constraints


@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    generator_type = data.get('generator_type', '')
    n = max(1, int(data.get('n', 10)))

    try:
        if generator_type == 'SimpleNameGenerator':
            languages = data.get('languages', [])
            kwargs = {
                'gender': data.get('gender', 'male'),
                'markov': float(data.get('markov', 0.5)),
                'pattern': data.get('pattern') or None,
                'name_part_type': data.get('name_part_type', 'given_name'),
            }
            kwargs.update(_collect_constraints(data))
            gen = SimpleNameGenerator(*languages, **kwargs)
            no_repeat = bool(data.get('no_repeat', True))
            result = gen.generate(n, no_repeat=no_repeat)

        elif generator_type == 'PersonalNameGenerator':
            languages = data.get('languages', [])
            # name_pattern is a list of {part, order} objects sorted by order
            name_pattern_raw = data.get('name_pattern', [])
            name_pattern = [item['part'] for item in
                            sorted(name_pattern_raw, key=lambda x: int(x.get('order', 0)))]
            if not name_pattern:
                return jsonify({'error': 'Select at least one name part.'}), 400
            markov_raw = data.get('markov', {})
            markov = {part: float(markov_raw.get(part, 0.5)) for part in name_pattern}
            patterns_raw = data.get('name_part_patterns', {})
            name_part_patterns = {k: v for k, v in patterns_raw.items() if v}
            female_fraction = float(data.get('female_fraction', 0.5))
            gen = PersonalNameGenerator(
                *languages,
                name_pattern=name_pattern,
                markov=markov,
                name_part_patterns=name_part_patterns or None,
            )
            result = gen.generate(n, female_fraction=female_fraction)

        elif generator_type == 'PlaceNameGenerator':
            languages = data.get('languages', [])
            kwargs = {
                'pattern': data.get('pattern') or None,
                'place_categories': data.get('place_categories', []),
            }
            kwargs.update(_collect_constraints(data))
            gen = PlaceNameGenerator(*languages, **kwargs)
            result = gen.generate(n)

        elif generator_type == 'CompanyNameGenerator':
            languages = data.get('languages', [])
            kwargs = {
                'pattern': data.get('pattern') or None,
                'industries': data.get('industries', []),
            }
            kwargs.update(_collect_constraints(data))
            gen = CompanyNameGenerator(*languages, **kwargs)
            result = gen.generate(n)

        elif generator_type == 'TribalNameGenerator':
            languages = data.get('languages', [])
            kwargs = {
                'markov': float(data.get('markov', 0.5)),
                'pattern': data.get('pattern') or None,
            }
            kwargs.update(_collect_constraints(data))
            gen = TribalNameGenerator(*languages, **kwargs)
            no_repeat = bool(data.get('no_repeat', True))
            result = gen.generate(n, no_repeat=no_repeat)

        else:
            return jsonify({'error': f'Unknown generator type: {generator_type}'}), 400

        return jsonify({'result': result})

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
