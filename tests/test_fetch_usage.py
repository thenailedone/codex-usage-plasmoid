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
        self.assertEqual([window["remainingPercent"] for window in result["windows"]], [75, 40])
        self.assertEqual(result["windows"][0]["windowDurationMins"], 300)
        self.assertEqual(result["credits"]["balance"], "12.50")

    def test_multi_bucket_limits_are_flattened_without_legacy_duplicates(self):
        payload = {
            "rateLimits": {
                "limitId": "legacy",
                "primary": {"usedPercent": 99, "windowDurationMins": 60},
            },
            "rateLimitsByLimitId": {
                "codex": {
                    "limitId": "codex",
                    "primary": {"usedPercent": 10, "windowDurationMins": 180},
                    "secondary": {"usedPercent": 20, "windowDurationMins": 20160},
                },
                "special": {
                    "limitId": "special",
                    "limitName": "Special models",
                    "primary": {"usedPercent": 30, "windowDurationMins": 1440},
                },
            },
        }
        result = MODULE.normalise_limits(payload)
        self.assertEqual(len(result["windows"]), 3)
        self.assertEqual(
            [window["windowDurationMins"] for window in result["windows"]],
            [180, 20160, 1440],
        )
        self.assertEqual(result["windows"][2]["limitName"], "Special models")

    def test_single_or_no_window_is_valid(self):
        one = MODULE.normalise_limits(
            {"rateLimits": {"primary": {"usedPercent": 12, "windowDurationMins": 60}}}
        )
        self.assertEqual(len(one["windows"]), 1)
        self.assertEqual(one["windows"][0]["remainingPercent"], 88)

        none = MODULE.normalise_limits({})
        self.assertEqual(none["windows"], [])
        self.assertEqual(none["state"], "ready")

    def test_auth_url_validation(self):
        self.assertEqual(
            MODULE.safe_auth_url("https://chatgpt.com/auth/login"),
            "https://chatgpt.com/auth/login",
        )
        with self.assertRaises(MODULE.BridgeError):
            MODULE.safe_auth_url("https://example.com/steal")


if __name__ == "__main__":
    unittest.main()
