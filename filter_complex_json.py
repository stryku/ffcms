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
        return ';\n'.join(self._filters)


def get_input_mapping_filters(definitions):
    filters = []

    i = 0
    for entry in definitions['inputs']:
        raw_input = '[{}:v]'.format(i)
        output_id = LINK_ID_TEMPLATE.format(entry['id'])
        filter = FILTER_TEMPLATE.format(inputs=raw_input, filter='', output=output_id)
        filters.append(filter)
        i += 1

    return filters


def join_link_ids(ids):
    link_ids = []

    for link_id in ids:
        link_ids.append(LINK_ID_TEMPLATE.format(link_id))

    return ''.join(link_ids)


def get_filtering_filters(definitions):
    filters = []

    for entry in definitions['filter']:
        inputs = join_link_ids(entry['inputs'])
        output_id = LINK_ID_TEMPLATE.format(entry['output'])

        f = FILTER_TEMPLATE.format(inputs=inputs, filter=entry['filter'], output=output_id)
        filters.append(f)

    return filters


def json_to_filter_complex(json_str):
    builder = FilterComplexBuilder()

    definitions = json.loads(json_str)

    for f in get_input_mapping_filters(definitions):
        builder.with_filter(f)

    for f in get_filtering_filters(definitions):
        builder.with_filter(f)

    return builder.build()


test_json = open('test.json', 'r').read()

result = json_to_filter_complex(test_json)
print(result)

