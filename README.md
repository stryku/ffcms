# ffcms - FFmpeg's -filter_complex made simple
 
`ffcms` is a tool that helps to create a `FFmpeg` command that's supposed to use
[complex filtergraphs](https://ffmpeg.org/ffmpeg.html#Complex-filtergraphs).

As an input it takes JSON that describes what the command is supposed to do.
Based on the JSON it produces and prints a complete `FFmpeg` command that is ready to run.

# Why?
JSON format seems simpler to mange by humans and machines than the `FFmpeg`'s syntax of complex filtergraphs.

# Examples
(see [the article](http://stryku.pl/poetry/ffcms.html) for an introduction)

There's an example of creating a grid out of one video. You can find it here: [https://trac.ffmpeg.org/wiki/FilteringGuide#Multipleinputoverlayin2x2grid](https://trac.ffmpeg.org/wiki/FilteringGuide#Multipleinputoverlayin2x2grid).

The command used there is:
```
ffmpeg -f lavfi -i testsrc -f lavfi -i testsrc -f lavfi -i testsrc -f lavfi -i testsrc -filter_complex \
"[1:v]negate[a]; \
 [2:v]hflip[b]; \
 [3:v]edgedetect[c]; \
 [0:v][a]hstack=inputs=2[top]; \
 [b][c]hstack=inputs=2[bottom]; \
 [top][bottom]vstack=inputs=2[out]" -map "[out]" -c:v ffv1 -t 5 multiple_input_grid.avi
```

Equivalent JSON file that `ffcms` would convert to above command is:
```json
{
  "in": [
    {
      "id": "first_input",
      "file": "timelapse.mov"
    },
    {
      "id": "second_input",
      "file": "timelapse.mov"
    },
    {
      "id": "third_input",
      "file": "timelapse.mov"
    },
    {
      "id": "fourth_input",
      "file": "timelapse.mov"
    }
  ],

  "out": "timelapse_grid.avi",

  "filters": [
    {
      "in": "second_input",
      "filter": "negate",
      "out": "a"
    },
    {
      "in": "third_input",
      "filter": "hflip",
      "out": "b"
    },
    {
      "in": "fourth_input",
      "filter": "edgedetect",
      "out": "c"
    },
    {
      "in": [
        "first_input",
        "a"
      ],
      "filter": "hstack",
      "out": "top"
    },
    {
      "in": [
        "b",
        "c"
      ],
      "filter": "hstack",
      "out": "bottom"
    },
    {
      "in": [
        "top",
        "bottom"
      ],
      "filter": "vstack",
      "out": "out"
    }
  ]
}
```

## "in"
The top-level `"in"` is an array of inputs that you'd pass after `-i` argument to `ffmpeg` binary. They are in the same order as you'd write them in the command line. It's used to let `ffcms` know what the input media files are and to assign a meaningful `"id"`s to the files. Thanks to that, in `"filters"` you can refer to them using e.g. `first_input`, not `0:v`.

## "out"
The top-level `"out"` is just the name of the output video.

## "filters"
The top-level `"filters"` are the filters that you'd write in the string provided to `-filter_complex` argument.

E.g. the first filter:
```json
{
    "in": "second_input",
    "filter": "negate",
    "out": "a"
}
```

is equivalent of the `[1:v]negate[a]` filter in `-filter_complex`'s string.

Mind the `hstack` and `vstack` filters. In `-filter_complex` string you need to pass number of inputs like: `[b][c]hstack=inputs=2[bottom]`. In `ffcms` JSON you write:
```json
{
    "in": [
        "b",
        "c"
    ],
    "filter": "hstack",
    "out": "bottom"
}
```
