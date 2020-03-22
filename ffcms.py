import json
import argparse

LINK_ID_TEMPLATE = '[{}]'


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
        filter_template = '{inputs}{filter}{output}'

        inputs_str = self._id_manager.join_link_ids(inputs)
        output_str = LINK_ID_TEMPLATE.format(output)
        return filter_template.format(inputs=inputs_str, filter=filter_str, output=output_str)


class Ffcms:
    def __init__(self, definitions):
        self._definitions = definitions

        self._id_manager = IdManager(definitions=self._definitions)
        self._filter_string_creator = FilterStringCreator(id_manager=self._id_manager)

    def create_filter_complex(self):
        filters = [f for f in self._get_filtering_filters()]
        return ';'.join(filters)

    def create_ffmpeg_command(self, command_template=None):
        if command_template is None:
            command_template = 'ffmpeg -y {inputs} -filter_complex "{filter_complex_str}" -map "{filter_complex_out}" -c:v ffv1 {output_file_name}'

        input_files = ' '.join(['-i ' + entry['file'] for entry in self._definitions['in']])
        filter_complex_str = self.create_filter_complex()
        filter_complex_output = LINK_ID_TEMPLATE.format(self._definitions['filters'][-1]['out'])
        output_file_name = self._definitions['out']

        return command_template.format(inputs=input_files, filter_complex_str=filter_complex_str,
                                       filter_complex_out=filter_complex_output, output_file_name=output_file_name)

    def _get_filtering_filters(self):
        filters = []

        for entry in self._definitions['filters']:
            entry_filter = entry['filter']
            if type(entry_filter) is str:
                entry_filter = {'name': entry_filter}

            entry_in = entry['in']
            if type(entry_in) is str:
                entry_in = [entry_in]

            f = self._filter_string_creator.create(entry_in, entry_filter, entry['out'])
            filters.append(f)

        return filters


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input',
                        help='The input for Ffcms. It can be a string input or a path to a file with the string input.')
    parser.add_argument('--filter_complex', help='Print only -filter_complex string', action='store_true')

    args = parser.parse_args()

    input = args.input
    if args.input[0] != '{':
        with open(args.input, 'r') as f:
            input = f.read()

    ffcms = Ffcms(json.loads(input))

    if args.filter_complex:
        print(ffcms.create_filter_complex())
    else:
        print(ffcms.create_ffmpeg_command())
