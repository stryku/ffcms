import json


"""
ffmpeg -y -i shord_behemot.mov -i shord_behemot.mov -i shord_behemot.mov -i shord_behemot.mov -filter_complex \      
"[1:v]negate[a]; \
 [2:v]hflip[b]; \
 [3:v]edgedetect[c]; \
 [0:v][a]hstack=inputs=2[top]; \
 [b][c]hstack=inputs=2[bottom]; \
 [top][bottom]vstack=inputs=2[out]" -map "[out]" -c:v ffv1  multiple_input_grid.avi
"""

FILTER_TEMPLATE = '{inputs}{filter}{output}'
LINK_ID_TEMPLATE = '[{}]'


class FilterComplexBuilder:
    def __init__(self):
        self._filters = []

    def with_filter(self, f):
        self._filters.append(f)

    def build(self):
        return ';'.join(self._filters)


class FilterStringCreator:
    def __init__(self):
        self._simple_filters = [
            'negate',
            'hflip',
            'edgedetect'
        ]

    def create(self, inputs, filter_name, output):
        if filter_name in self._simple_filters:
            return self._create_simple_filter(inputs, filter_name, output)
        elif filter_name == 'hstack':
            return self._create_stack(inputs, output, 'h')
        elif filter_name == 'vstack':
            return self._create_stack(inputs, output, 'v')

    def _create_stack(self, inputs, output, stack_letter):
        stack = '{}stack=inputs={}'.format(stack_letter, len(inputs))
        return self._create_filter(inputs, stack, output)

    def _create_simple_filter(self, inputs, filter_name, output):
        return self._create_filter(inputs, filter_name, output)

    @staticmethod
    def _create_filter(inputs, filter_str, output):
        inputs_str = join_link_ids(inputs)
        output_str = LINK_ID_TEMPLATE.format(output)
        return FILTER_TEMPLATE.format(inputs=inputs_str, filter=filter_str, output=output_str)


def join_link_ids(ids):
    link_ids = []

    for link_id in ids:
        link_ids.append(LINK_ID_TEMPLATE.format(link_id))

    return ''.join(link_ids)


def get_filtering_filters(definitions):
    filters = []

    for entry in definitions['filter']:
        f = FilterStringCreator().create(entry['inputs'], entry['filter'], entry['output'])
        filters.append(f)

    return filters


def definitions_to_filter_complex(definitions):
    builder = FilterComplexBuilder()

    for f in get_filtering_filters(definitions):
        builder.with_filter(f)

    return builder.build()


def create_ffmpeg_command(json_str):
    command_template = 'ffmpeg -y {} -filter_complex "{}" -map "{}" -c:v ffv1 {}'

    definitions = json.loads(json_str)

    input_files = ' '.join(['-i ' + entry['file'] for entry in definitions['inputs']])
    filter_complex_str = definitions_to_filter_complex(definitions)
    filter_complex_output = LINK_ID_TEMPLATE.format(definitions['filter'][-1]['output'])
    output_file_name = definitions['output']

    return command_template.format(input_files, filter_complex_str, filter_complex_output, output_file_name)


with open('test.json', 'r') as f:
    test_json = f.read()

result = create_ffmpeg_command(test_json)
print(result)



