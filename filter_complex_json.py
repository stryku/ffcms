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

"""
ffmpeg -i input.mp4 -i image.png \
-filter_complex "[0:v][1:v] overlay=25:25:enable='between(t,0,20)'" \
-pix_fmt yuv420p -c:a copy \
output.mp4
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


class IdManager:
    def __init__(self, definitions):
        self._definitions = definitions

    def map_id(self, id_to_map):
        i = 0
        for entry in self._definitions['in']:
            if id_to_map == entry['id']:
                return '{}:v'.format(i)

            i += 1

        return id_to_map

    def join_link_ids(self, ids):
        link_ids = []

        for link_id in ids:
            link_id = self.map_id(link_id)
            link_ids.append(LINK_ID_TEMPLATE.format(link_id))

        return ''.join(link_ids)


class FilterStringCreator:
    def __init__(self, id_manager):
        self._id_manager = id_manager

        self._simple_filters = [
            'negate',
            'hflip',
            'edgedetect'
        ]

    def create(self, inputs, filter_definition, output):
        name = filter_definition['name']
        if name in self._simple_filters:
            return self._create_simple_filter(inputs, filter_definition, output)
        elif name == 'hstack':
            return self._create_stack(inputs, output, 'h')
        elif name == 'vstack':
            return self._create_stack(inputs, output, 'v')
        elif name == 'overlay':
            return self._create_overlay(inputs, filter_definition, output)

    def _create_overlay(self, inputs, filter_definition, output):
        params = ['{}={}'.format(name, value) for name, value in filter_definition['params'].items()]
        overlay = 'overlay={}'.format(':'.join(params))
        return self._create_filter(inputs, overlay, output)

    def _create_stack(self, inputs, output, stack_letter):
        stack = '{}stack=inputs={}'.format(stack_letter, len(inputs))
        return self._create_filter(inputs, stack, output)

    def _create_simple_filter(self, inputs, filter_definition, output):
        return self._create_filter(inputs, filter_definition['name'], output)

    def _create_filter(self, inputs, filter_str, output):
        inputs_str = self._id_manager.join_link_ids(inputs)
        output_str = LINK_ID_TEMPLATE.format(output)
        return FILTER_TEMPLATE.format(inputs=inputs_str, filter=filter_str, output=output_str)


class Ffcms:
    def get_filtering_filters(self, definitions):
        filters = []

        id_manager = IdManager(definitions)

        for entry in definitions['filters']:
            entry_filter = entry['filter']
            if type(entry_filter) is str:
                entry_filter = {'name': entry_filter}

            entry_in = entry['in']
            if type(entry_in) is str:
                entry_in = [entry_in]

            f = FilterStringCreator(id_manager=id_manager) \
                .create(entry_in, entry_filter, entry['out'])
            filters.append(f)

        return filters

    def definitions_to_filter_complex(self, definitions):
        builder = FilterComplexBuilder()

        for f in self.get_filtering_filters(definitions):
            builder.with_filter(f)

        return builder.build()

    def create_ffmpeg_command(self, json_str):
        command_template = 'ffmpeg -y {} -filter_complex "{}" -map "{}" -c:v ffv1 {}'

        definitions = json.loads(json_str)

        input_files = ' '.join(['-i ' + entry['file'] for entry in definitions['in']])
        filter_complex_str = self.definitions_to_filter_complex(definitions)
        filter_complex_output = LINK_ID_TEMPLATE.format(definitions['filters'][-1]['out'])
        output_file_name = definitions['out']

        return command_template.format(input_files, filter_complex_str, filter_complex_output, output_file_name)


with open('test_first.json', 'r') as f:
    test_json = f.read()

result = Ffcms().create_ffmpeg_command(test_json)
print(result)
