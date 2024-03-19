from typing import List


def _fix_image_paths(data: list) -> List[dict]:
    """Rewrite image urls to use the scale name.

    This is not ideal in terms of performance, but
    it 'works' for imported content.
    """
    parsed = []
    for info in data:
        image_scales = info["image_scales"]
        for field in image_scales:
            field_data = image_scales[field][0]
            field_data["download"] = f"@@images/{field}"
            for key, scale in field_data["scales"].items():
                scale["download"] = f"@@images/{field}/{key}"
        parsed.append(info)
    return parsed


def _fix_grid_block(block: dict) -> dict:
    """Remove references to computed scales in images."""
    for column in block["columns"]:
        for key in ("preview_image", "image"):
            image_data = column.get(key)
            if not image_data:
                continue
            column[key] = _fix_image_paths(image_data)
    return block


BLOCKS_HANDLERS = {
    "__grid": _fix_grid_block,
    "grid": _fix_grid_block,
}


def parse_blocks(blocks: dict) -> dict:
    """Clean up blocks."""
    parsed = {}
    for block_uid, block in blocks.items():
        type_ = block.get("@type")
        func = BLOCKS_HANDLERS.get(type_, None)
        block = func(block) if func else block
        parsed[block_uid] = block
    return parsed
