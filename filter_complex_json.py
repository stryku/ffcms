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



class FilterComplexBuilder:
    def __init__(self):
        self._filters = []

    def with_filter(self, f):
        self._filters.append(f)

    def build(self):
        return ';\n'.join(self._filters)

        
def json_to_filter_complex(json_str):
    builder = FilterComplexBuilder()

    definitions = json.loads(json_str)

    filter_template = '{inputs}{filter}{output}'

    i = 0
    for entry in definitions['inputs']:
        raw_input = '[{}:v]'.format(i)
        output_id = '[{}]'.format(entry['id'])
        filter = filter_template.format(inputs=raw_input, filter='', output=output_id)
        builder.with_filter(filter)
        i += 1

    return builder.build()


test_json = open('test.json', 'r').read()

result = json_to_filter_complex(test_json)
print(result)

