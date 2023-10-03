import xml.etree.ElementTree as ET
import logging

ns = {'x': 'x'}
speech_parts = {
    'adj': 'adj.',
    'adv': 'adv.',
    'konj': 'conj.',
    'num': 'num.',
    'prep': 'prep.',
    'postp': 'postp.',
    'prop': 'prop.',
    's': 'n.',
    'v': 'verb.'
}


class Example:
    origin = ''
    translation = ''


class Definition:
    translation = ''
    comment = ''
    examples = []


class Article:
    key = ''
    speech_part = ''
    grammar = ''
    definitions = []
    idioms = []


current_article = ''


def grammar_to_xdxf(grammar):
    if not grammar:
        return ''
    return f'<i>{grammar}</i>'


def idioms_to_xdxf(idioms):
    if not idioms:
        return ''
    idioms_str = '\n'
    for idiom in idioms:
        idioms_str += f'\t\t\t<ex type="phr"><b>{idiom.origin}</b> - {idiom.translation}</ex>'
        if idiom is not idioms[-1]:
            idioms_str += '\n'
    return idioms_str


def definitions_to_xdxf(definitions):
    counter = 1
    def_str = ''
    for definition in definitions:
        if len(definitions) > 1:
            def_str += f'{counter}) '
        def_str += f'<b>{definition.translation}</b>'
        if definition.comment:
            def_str += f' <i>({definition.comment})</i>'
        if definition.examples:
            def_str += '\n'
        for example in definition.examples:
            def_str += f'\t\t\t<ex>{example.origin} - {example.translation}</ex>'
            if example is not definition.examples[-1]:
                def_str += '\n'
        if counter is len(definitions) - 1:
            def_str += '\n\t\t\t'
        counter = counter + 1
    return def_str


def article_to_xdxf(parsed_article):
    if parsed_article.key is '' or not parsed_article.definitions:
        return ''
    article_txt = f'''      <ar>
            <k>{parsed_article.key}</k>
            <gr>{parsed_article.speech_part} {grammar_to_xdxf(parsed_article.grammar)}</gr>
            {definitions_to_xdxf(parsed_article.definitions)}{idioms_to_xdxf(parsed_article.idioms)}
          </ar>
    '''
    return article_txt


def parse_key(key: ET.Element):
    if key is None:
        return ''
    return key.text


def parse_speech_part(speech_part: ET.Element):
    if speech_part is None:
        return ''
    speech_part_mark = speech_parts.get(speech_part.text)
    if speech_part_mark is None:
        return ''
    return speech_part_mark


def parse_grammar(grammar: ET.Element):
    if grammar is None:
        return ''
    grammar_text = grammar.text.replace('_&_', ' ~ ')
    return grammar_text


def cleanup(s):
    return s.replace('"', '').replace('&v;', '~').replace('*', '').replace('\n', '').strip()


def parse_origin(origin: ET.Element):
    if origin is None:
        return ''
    full_text = " ".join(origin.itertext())
    for government in origin.findall('x:r', ns):
        full_text = full_text.replace(government.text, f'[{government.text}]')

    return full_text


def parse_translation(translation: ET.Element):
    if translation is None:
        return ''
    full_text = " ".join(translation.itertext())
    for government in translation.findall('x:xr', ns):
        full_text = full_text.replace(government.text, f'[{government.text}]')

    return full_text


def parse_example(example: ET.Element):
    parsed_example = Example()
    parsed_example.origin = cleanup(parse_origin(example.find('x:n', ns)))
    parsed_example.translation = cleanup(parse_translation(example.find('x:qnp/x:qng/x:qn', ns)))
    return parsed_example


def parse_examples(examples: ET.Element):
    if examples is None:
        return []
    examples_parsed = []
    for example in examples.findall('x:ng', ns):
        examples_parsed.append(parse_example(example))
    return examples_parsed


def parse_definition(definition: ET.Element):
    definition_parsed = Definition()
    comments = []
    for comment in definition.findall('x:tg/x:dg/x:d', ns):
        comments.append(comment.text)
    translations = []
    for translation in definition.findall('x:tg/x:xp/x:xg/x:x',ns):
        translations.append(cleanup(parse_translation(translation)))
    definition_parsed.comment = ', '.join(comments)
    definition_parsed.translation = ', '.join(translations)
    definition_parsed.examples = parse_examples(definition.find('x:np', ns))
    return definition_parsed


def parse_definitions(definitions: ET.Element):
    if definitions is None:
        return []
    definitions_parsed = []
    for definition in definitions.findall('x:tp', ns):
        definitions_parsed.append(parse_definition(definition))
    return definitions_parsed


def parse_idiom(idiom: ET.Element):
    parsed_idiom = Example()
    parsed_idiom.origin = cleanup(parse_origin(idiom.find('x:f', ns)))
    parsed_idiom.translation = cleanup(parse_translation(idiom.find('x:fqnp/x:fqng/x:qf', ns)))
    return parsed_idiom


def parse_idioms(idioms: ET.Element):
    if idioms is None:
        return []
    idioms_parsed = []
    for idiom in idioms.findall('x:fg', ns):
        idioms_parsed.append(parse_idiom(idiom))
    return idioms_parsed


def parse_article(article_xml):
    article_xml = article_xml.replace('<x:A ', '<x:A xmlns:x="x" ').replace('<x:A>', '<x:A xmlns:x="x">')
    global current_article
    # to facilitate copy article for debugging remove namespace
    current_article = article_xml.replace('<x:A xmlns:x="x" ', '<x:A ')
    a = Article()
    try:
        root = ET.fromstring(article_xml)
        a.key = parse_key(root.find('./x:P/x:mg/x:m', ns))
        if a.key is '':
            logging.error(f'Key error! Article {article_xml} has no key')
        a.speech_part = parse_speech_part(root.find('./x:P/x:mg/x:sl', ns))
        a.grammar = parse_grammar(root.find('./x:P/x:mg/x:grg/x:mv', ns))
        a.definitions = parse_definitions(root.find('./x:S', ns))
        a.idioms = parse_idioms(root.find('./x:F', ns))
    except:
        logging.error(f'Parse error. Article: {current_article}')
    if not a.definitions:
        logging.error(f'Definitions error! Article {current_article} has no definitions')
    return a


def skip_article(a: Article):
    if not a.key:
        return True

    for definition in a.definitions:
        if definition.translation:
            return False
    return True


if __name__ == "__main__":
    filename = 'resources/eki_example.xml'
    out_filename = 'est_rus.xdxf'
    xdxf_header = '''<?xml version="1.0" encoding="UTF-8" ?>
    <xdxf revision="34">
        <meta_info>
            <languages>
                <from xml:lang="EST"/>
                <to xml:lang="RUS"/>
            </languages>
            <title>Eesti-Vene EKI sõnastik</title>
            <description>Eesti-Vene sõnastik converted from http://www.eki.ee/dict/evs/</description>
            <file_ver>1.0</file_ver>
            <creation_date>2-Oct-2023</creation_date>
            <last_edited_date>2-Oct-2023</last_edited_date>
        </meta_info>
        <lexicon>
    '''
    xdxf_footer = '''    </lexicon>
</xdxf>'''
    with open(out_filename,'w', encoding='utf-8') as out_file:
        out_file.write(xdxf_header)
        with open(filename) as file:
            article = ''
            in_article = False
            for line in file:
                if '<x:A' in line:
                    in_article = True
                if in_article:
                    article = article + line
                if '</x:A>' in line:
                    a = parse_article(article)
                    if not skip_article(a):
                        out_file.write(article_to_xdxf(a))
                    in_article = False
                    article = ''
        out_file.write(xdxf_footer)
