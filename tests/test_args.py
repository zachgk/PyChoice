import pychoice as choice


@choice.args()
def echo(f):
    return f


def test_foo():
    assert echo("foo") == "foo"
    assert "echo" in choice.registry
