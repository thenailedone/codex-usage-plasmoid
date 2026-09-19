import importlib.util
import pathlib
import unittest


HELPER = pathlib.Path(__file__).parents[1] / "package/contents/code/fetch_usage.py"
SPEC = importlib.util.spec_from_file_location("fetch_usage", HELPER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FetchUsageTests(unittest.TestCase):
    def test_remaining_is_clamped(self):
        self.assertEqual(MODULE.remaining({"usedPercent": -10})["remainingPercent"], 100)
        self.assertEqual(MODULE.remaining({"usedPercent": 40.5})["remainingPercent"], 60)
        self.assertEqual(MODULE.remaining({"usedPercent": 120})["remainingPercent"], 0)

    def test_normalise_limits(self):
        payload = {
            "rateLimits": {
                "primary": {"usedPercent": 25, "windowDurationMins": 300, "resetsAt": 123},
                "secondary": {"usedPercent": 60, "windowDurationMins": 10080, "resetsAt": 456},
                "credits": {"hasCredits": True, "unlimited": False, "balance": "12.50"},
            }
        }
        result = MODULE.normalise_limits(payload)
        self.assertEqual(result["primary"]["remainingPercent"], 75)
        self.assertEqual(result["secondary"]["remainingPercent"], 40)
        self.assertEqual(result["credits"]["balance"], "12.50")

    def test_auth_url_validation(self):
        self.assertEqual(
            MODULE.safe_auth_url("https://chatgpt.com/auth/login"),
            "https://chatgpt.com/auth/login",
        )
        with self.assertRaises(MODULE.BridgeError):
            MODULE.safe_auth_url("https://example.com/steal")


if __name__ == "__main__":
    unittest.main()
