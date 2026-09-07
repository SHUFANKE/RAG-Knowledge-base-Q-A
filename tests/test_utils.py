from app.utils import add,clean_text


def test_add():
    assert add(2,3) == 5
    assert add(-1,1) == 0

def test_clean_text():
    raw_text = " Python Engineering "
    expected = "python engineering"
    assert clean_text(raw_text) == expected