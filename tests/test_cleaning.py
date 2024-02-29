from miso_tool.cleaning import fix_lsts_sample_name


def test_fix_lsts_sample_name():
    testcases = [
        ("WIN-AH-2021-OTH-1-1", "WIN-AH-2021-OTH-0001-1"),
        ("WIN-AH-2021-OTH-123-1-1", "WIN-AH-2021-OTH-0123-1-1"),
        ("WIN-AH-2021-OTH-0023-a bunch of words", "WIN-AH-2021-OTH-0023-a-bunch-of-words"),
        ("2021-OTH-1-(shh) - it's a secret!", "WIN-AH-2021-OTH-0001-shh-it-s-a-secret"),
        ("2021-OTH-1-1", "WIN-AH-2021-OTH-0001-1"),
        ("nothing wrong here", "nothing-wrong-here"),
        ("another #$%^&*()+sample", "another-sample"),
    ]
    for observed, expected in testcases:
        assert fix_lsts_sample_name(observed) == expected
