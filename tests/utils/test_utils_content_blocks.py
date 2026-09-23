from plone.exportimport.utils.content import blocks

import pytest


def _image_info(**extra) -> dict:
    info = {
        "@id": "/image",
        "image_scales": {
            "image": [
                {
                    "download": "http://localhost/image/@@images/image-800-abc.png",
                    "scales": {
                        "thumb": {
                            "download": "http://localhost/image/@@images/thumb.png"
                        },
                    },
                }
            ]
        },
    }
    info.update(extra)
    return info


def test_fix_image_paths():
    func = blocks._fix_image_paths
    result = func([_image_info()])
    field_data = result[0]["image_scales"]["image"][0]
    assert field_data["download"] == "@@images/image"
    assert field_data["scales"]["thumb"]["download"] == "@@images/image/thumb"


@pytest.mark.parametrize(
    "info",
    [
        {"@id": "/image"},
        {"@id": "/image", "image_scales": None},
        {"@id": "/image", "image_scales": {}},
        {"@id": "/image", "image_scales": {"image": []}},
        {"@id": "/image", "image_scales": {"image": [{"download": "foo.png"}]}},
    ],
)
def test_fix_image_paths_incomplete_data(info: dict):
    func = blocks._fix_image_paths
    result = func([info])
    assert result == [info]


@pytest.mark.parametrize("block_type", ["__grid", "grid"])
def test_parse_blocks_grid_without_image_scales(block_type: str):
    data = {
        "block-1": {
            "@type": block_type,
            "columns": [
                {"@type": "teaser", "preview_image": [{"@id": "/image"}]},
                {"@type": "image", "image": [_image_info()]},
                {"@type": "slate"},
            ],
        }
    }
    result = blocks.parse_blocks(data)
    columns = result["block-1"]["columns"]
    assert columns[0]["preview_image"] == [{"@id": "/image"}]
    field_data = columns[1]["image"][0]["image_scales"]["image"][0]
    assert field_data["download"] == "@@images/image"
