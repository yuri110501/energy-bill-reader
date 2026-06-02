from core.id_sof_utils import _normalize_codigo_cliente, get_id_sof_from_codigo


def test_normalize_codigo_cliente_removes_separators():
    assert _normalize_codigo_cliente("0087359-4") == "00873594"
    assert _normalize_codigo_cliente("0439304-0") == "04393040"
    assert _normalize_codigo_cliente("  70.398.246/52 ") == "7039824652"


def test_get_id_sof_from_codigo_matches_hyphenless_variants():
    assert get_id_sof_from_codigo("00873594") == "SOF - 0001.0069"
    assert get_id_sof_from_codigo("04393040") == "SOF - 0001.0068"
    assert get_id_sof_from_codigo("4393040") == "SOF - 0001.0068"


def test_get_id_sof_from_codigo_handles_raw_mapping_keys():
    assert get_id_sof_from_codigo("0087359-4") == "SOF - 0001.0069"
    assert get_id_sof_from_codigo("0439304-0") == "SOF - 0001.0068"
