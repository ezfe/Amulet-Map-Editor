from amulet.operations.delete_chunk import delete_chunk

export = {
    "v": 1,  # a version 1 plugin
    "name": "Delete Chunks",  # the name of the plugin
    "features": ["src_selection"],
    "inputs": ["src_selection"],  # the inputs to give to the plugin
    "operation": delete_chunk  # the actual function to call when running the plugin
}
