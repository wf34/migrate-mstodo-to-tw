# Migrate Microsoft TODOs to Taskwarrior
[Taskwarrior](https://taskwarrior.org) is an open source, self-hosted (or fully local) task tracker that often gets recommended as an alternative to proprietary SaaS task trackers.
1. MS permits the data to be exported in a single binary PST file
2. [libpff](https://github.com/libyal/libpff) can operate on that format
3. `pffexport -t decoded_todos -d my-todos.pst`, where `-d` is essential: libpff doesn't properly parse custom field types (I understand, it's mostly used for outlook's email archives, which are also exported via PST). An example of custom type: `IOpenTypedFacet.Com_Microsoft_Todo_Subtasks`. Highly likely, that preserving the subtasks is preferred during export
4. `./tasks_to_jsons.py --input_dir decoded_todos --output_file 4tw.json`
5. `task import 4tw.json`
