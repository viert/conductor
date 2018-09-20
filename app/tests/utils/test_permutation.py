from unittest import TestCase
from library.engine.permutation import succ, sequence, expand_pattern_with_vars

class TestPermutation(TestCase):
    """Test cases created from ruby console"""
    SUCC_CASES = {
        "0": "1",
        "a": "b",
        "D": "E",
        "9z": "10a",
        "D9jzZ": "D9kaA"
    }

    SEQUENCE_CASES = (
        ("0", "15", ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]),
        ("03", "12", ["03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]),
        ("0a", "z9", ["0a", "0b", "0c", "0d", "0e", "0f", "0g", "0h", "0i", "0j", "0k", "0l", "0m", "0n", "0o", "0p", "0q", "0r", "0s", "0t", "0u", "0v", "0w", "0x", "0y", "0z", "1a", "1b", "1c", "1d", "1e", "1f", "1g", "1h", "1i", "1j", "1k", "1l", "1m", "1n", "1o", "1p", "1q", "1r", "1s", "1t", "1u", "1v", "1w", "1x", "1y", "1z", "2a", "2b", "2c", "2d", "2e", "2f", "2g", "2h", "2i", "2j", "2k", "2l", "2m", "2n", "2o", "2p", "2q", "2r", "2s", "2t", "2u", "2v", "2w", "2x", "2y", "2z", "3a", "3b", "3c", "3d", "3e", "3f", "3g", "3h", "3i", "3j", "3k", "3l", "3m", "3n", "3o", "3p", "3q", "3r", "3s", "3t", "3u", "3v", "3w", "3x", "3y", "3z", "4a", "4b", "4c", "4d", "4e", "4f", "4g", "4h", "4i", "4j", "4k", "4l", "4m", "4n", "4o", "4p", "4q", "4r", "4s", "4t", "4u", "4v", "4w", "4x", "4y", "4z", "5a", "5b", "5c", "5d", "5e", "5f", "5g", "5h", "5i", "5j", "5k", "5l", "5m", "5n", "5o", "5p", "5q", "5r", "5s", "5t", "5u", "5v", "5w", "5x", "5y", "5z", "6a", "6b", "6c", "6d", "6e", "6f", "6g", "6h", "6i", "6j", "6k", "6l", "6m", "6n", "6o", "6p", "6q", "6r", "6s", "6t", "6u", "6v", "6w", "6x", "6y", "6z", "7a", "7b", "7c", "7d", "7e", "7f", "7g", "7h", "7i", "7j", "7k", "7l", "7m", "7n", "7o", "7p", "7q", "7r", "7s", "7t", "7u", "7v", "7w", "7x", "7y", "7z", "8a", "8b", "8c", "8d", "8e", "8f", "8g", "8h", "8i", "8j", "8k", "8l", "8m", "8n", "8o", "8p", "8q", "8r", "8s", "8t", "8u", "8v", "8w", "8x", "8y", "8z", "9a", "9b", "9c", "9d", "9e", "9f", "9g", "9h", "9i", "9j", "9k", "9l", "9m", "9n", "9o", "9p", "9q", "9r", "9s", "9t", "9u", "9v", "9w", "9x", "9y", "9z"]),
        ("j3", "m8", ["j3", "j4", "j5", "j6", "j7", "j8", "j9", "k0", "k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9", "l0", "l1", "l2", "l3", "l4", "l5", "l6", "l7", "l8", "l9", "m0", "m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"])
    )

    VARS_CASES = (
        ("a[01-03][a,b]", [
            ("a01a", ["a01a", "01", "a"]),
            ("a01b", ["a01b", "01", "b"]),
            ("a02a", ["a02a", "02", "a"]),
            ("a02b", ["a02b", "02", "b"]),
            ("a03a", ["a03a", "03", "a"]),
            ("a03b", ["a03b", "03", "b"]),
        ]),
    )

    def test_succ(self):
        for i, nx in self.SUCC_CASES.items():
            self.assertEqual(succ(i), nx)

    def test_sequence(self):
        for fr, to, res in self.SEQUENCE_CASES:
            self.assertItemsEqual(res, sequence(fr, to))

    def test_expand_with_vars(self):
        for pattern, results in self.VARS_CASES:
            actual = list(expand_pattern_with_vars(pattern))

            self.assertEqual(len(results), len(actual))
            for i in xrange(len(results)):
                self.assertEqual(results[i][0], actual[i][0])       # result pattern
                self.assertItemsEqual(results[i][1], actual[i][1])  # result vars
