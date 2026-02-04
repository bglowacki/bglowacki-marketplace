"""Tests for outdated plugin and stale cache detection."""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import base64

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))

from collect_usage import check_stale_cache, check_outdated_plugins, compute_pre_computed_findings


class TestStaleCache:
    """Tests for stale cache detection."""

    def test_detects_temp_git_directories(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "temp_git_123_abc").mkdir()
        (cache / "temp_git_456_def").mkdir()
        (cache / "real-marketplace").mkdir()

        result = check_stale_cache(cache, tmp_path / "settings.json")

        temps = [r for r in result if r["type"] == "temp_leftover"]
        assert len(temps) == 2
        assert {t["path"] for t in temps} == {"temp_git_123_abc", "temp_git_456_def"}

    def test_detects_old_version_directories(self, tmp_path):
        cache = tmp_path / "cache"
        mp = cache / "my-marketplace" / "my-plugin"
        mp.mkdir(parents=True)
        for v in ["1.0.0", "1.1.0", "2.0.0"]:
            (mp / v).mkdir()

        result = check_stale_cache(cache, tmp_path / "settings.json")

        old = [r for r in result if r["type"] == "old_versions"]
        assert len(old) == 1
        assert old[0]["plugin"] == "my-plugin"
        assert old[0]["marketplace"] == "my-marketplace"
        assert old[0]["active_version"] == "2.0.0"
        assert set(old[0]["old_versions"]) == {"1.0.0", "1.1.0"}
        assert old[0]["old_count"] == 2

    def test_single_version_not_flagged(self, tmp_path):
        cache = tmp_path / "cache"
        mp = cache / "my-marketplace" / "my-plugin"
        mp.mkdir(parents=True)
        (mp / "1.0.0").mkdir()

        result = check_stale_cache(cache, tmp_path / "settings.json")

        old = [r for r in result if r["type"] == "old_versions"]
        assert len(old) == 0

    def test_two_versions_not_flagged(self, tmp_path):
        """Only flag if >1 old version (i.e., 3+ total versions)."""
        cache = tmp_path / "cache"
        mp = cache / "my-marketplace" / "my-plugin"
        mp.mkdir(parents=True)
        (mp / "1.0.0").mkdir()
        (mp / "2.0.0").mkdir()

        result = check_stale_cache(cache, tmp_path / "settings.json")

        old = [r for r in result if r["type"] == "old_versions"]
        assert len(old) == 0

    def test_detects_orphaned_marketplaces(self, tmp_path):
        cache = tmp_path / "cache"
        (cache / "known-marketplace").mkdir(parents=True)
        (cache / "orphaned-marketplace").mkdir(parents=True)

        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "extraKnownMarketplaces": {
                "known-marketplace": {"source": {"source": "github", "repo": "owner/repo"}}
            }
        }))

        result = check_stale_cache(cache, settings)

        orphaned = [r for r in result if r["type"] == "orphaned_marketplace"]
        assert len(orphaned) == 1
        assert orphaned[0]["name"] == "orphaned-marketplace"

    def test_skips_hidden_directories(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / ".hidden").mkdir()

        result = check_stale_cache(cache, tmp_path / "settings.json")
        assert len(result) == 0

    def test_empty_cache_returns_empty(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()

        result = check_stale_cache(cache, tmp_path / "settings.json")
        assert result == []

    def test_nonexistent_cache_returns_empty(self, tmp_path):
        result = check_stale_cache(tmp_path / "nonexistent", tmp_path / "settings.json")
        assert result == []

    def test_commit_hash_versions_skipped(self, tmp_path):
        """Commit-hash version dirs (not semver) should not be flagged."""
        cache = tmp_path / "cache"
        mp = cache / "official" / "some-plugin"
        mp.mkdir(parents=True)
        (mp / "7caef65e1070").mkdir()
        (mp / "abc123def456").mkdir()

        result = check_stale_cache(cache, tmp_path / "settings.json")

        old = [r for r in result if r["type"] == "old_versions"]
        assert len(old) == 0

    def test_no_settings_file_skips_orphan_check(self, tmp_path):
        cache = tmp_path / "cache"
        (cache / "some-marketplace").mkdir(parents=True)

        result = check_stale_cache(cache, tmp_path / "nonexistent_settings.json")

        orphaned = [r for r in result if r["type"] == "orphaned_marketplace"]
        assert len(orphaned) == 0


class TestOutdatedPlugins:
    """Tests for remote version comparison."""

    def _make_cache(self, tmp_path, marketplace, plugin, version):
        """Helper to create a plugin cache structure."""
        plugin_dir = tmp_path / "cache" / marketplace / plugin / version
        plugin_dir.mkdir(parents=True)
        pjson = plugin_dir / ".claude-plugin"
        pjson.mkdir()
        (pjson / "plugin.json").write_text(json.dumps({"version": version}))
        return tmp_path / "cache"

    def _make_settings(self, tmp_path, marketplaces):
        """Helper to create settings.json."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "extraKnownMarketplaces": marketplaces
        }))
        return settings

    def _make_marketplace_json(self, cache, marketplace, plugins):
        """Helper to create marketplace.json in cache."""
        mp_dir = cache / marketplace / ".claude-plugin"
        mp_dir.mkdir(parents=True, exist_ok=True)
        (mp_dir / "marketplace.json").write_text(json.dumps({
            "name": marketplace,
            "plugins": [{"name": p, "source": f"./{p}"} for p in plugins]
        }))

    def _github_api_response(self, version):
        """Create a mock GitHub API response for plugin.json."""
        content = json.dumps({"version": version})
        encoded = base64.b64encode(content.encode()).decode()
        return json.dumps({"content": encoded}).encode()

    @patch("collect_usage.urllib.request.urlopen")
    def test_detects_outdated_plugin(self, mock_urlopen, tmp_path):
        cache = self._make_cache(tmp_path, "test-mp", "my-plugin", "1.0.0")
        settings = self._make_settings(tmp_path, {
            "test-mp": {"source": {"source": "github", "repo": "owner/repo"}}
        })
        self._make_marketplace_json(cache, "test-mp", ["my-plugin"])

        mock_resp = MagicMock()
        mock_resp.read.return_value = self._github_api_response("2.0.0")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = check_outdated_plugins(cache, settings)

        assert len(result) == 1
        assert result[0]["plugin"] == "my-plugin"
        assert result[0]["marketplace"] == "test-mp"
        assert result[0]["installed_version"] == "1.0.0"
        assert result[0]["latest_version"] == "2.0.0"

    @patch("collect_usage.urllib.request.urlopen")
    def test_up_to_date_plugin_not_flagged(self, mock_urlopen, tmp_path):
        cache = self._make_cache(tmp_path, "test-mp", "my-plugin", "2.0.0")
        settings = self._make_settings(tmp_path, {
            "test-mp": {"source": {"source": "github", "repo": "owner/repo"}}
        })
        self._make_marketplace_json(cache, "test-mp", ["my-plugin"])

        mock_resp = MagicMock()
        mock_resp.read.return_value = self._github_api_response("2.0.0")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = check_outdated_plugins(cache, settings)
        assert len(result) == 0

    @patch("collect_usage.urllib.request.urlopen")
    def test_api_error_gracefully_skipped(self, mock_urlopen, tmp_path):
        cache = self._make_cache(tmp_path, "test-mp", "my-plugin", "1.0.0")
        settings = self._make_settings(tmp_path, {
            "test-mp": {"source": {"source": "github", "repo": "owner/repo"}}
        })
        self._make_marketplace_json(cache, "test-mp", ["my-plugin"])

        mock_urlopen.side_effect = Exception("Network error")

        result = check_outdated_plugins(cache, settings)
        assert result == []

    def test_no_settings_returns_empty(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        result = check_outdated_plugins(cache, tmp_path / "nonexistent.json")
        assert result == []

    def test_marketplace_without_repo_skipped(self, tmp_path):
        cache = self._make_cache(tmp_path, "local-mp", "my-plugin", "1.0.0")
        settings = self._make_settings(tmp_path, {})

        result = check_outdated_plugins(cache, settings)
        assert result == []

    @patch("collect_usage.urllib.request.urlopen")
    def test_plugin_without_version_skipped(self, mock_urlopen, tmp_path):
        cache = tmp_path / "cache"
        mp = cache / "test-mp" / "no-ver-plugin" / "abc123"
        mp.mkdir(parents=True)
        # plugin.json without version field
        pjson_dir = mp / ".claude-plugin"
        pjson_dir.mkdir()
        (pjson_dir / "plugin.json").write_text(json.dumps({"name": "no-ver-plugin"}))

        settings = self._make_settings(tmp_path, {
            "test-mp": {"source": {"source": "github", "repo": "owner/repo"}}
        })
        self._make_marketplace_json(cache, "test-mp", ["no-ver-plugin"])

        result = check_outdated_plugins(cache, settings)
        assert result == []

    @patch("collect_usage.urllib.request.urlopen")
    def test_multiple_plugins_checked(self, mock_urlopen, tmp_path):
        cache = tmp_path / "cache"
        # Plugin A - outdated
        pa = cache / "test-mp" / "plugin-a" / "1.0.0"
        pa.mkdir(parents=True)
        (pa / ".claude-plugin").mkdir()
        (pa / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": "1.0.0"}))

        # Plugin B - up to date
        pb = cache / "test-mp" / "plugin-b" / "3.0.0"
        pb.mkdir(parents=True)
        (pb / ".claude-plugin").mkdir()
        (pb / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": "3.0.0"}))

        settings = self._make_settings(tmp_path, {
            "test-mp": {"source": {"source": "github", "repo": "owner/repo"}}
        })
        self._make_marketplace_json(cache, "test-mp", ["plugin-a", "plugin-b"])

        def side_effect(req, timeout=None):
            mock_resp = MagicMock()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            url = req.full_url if hasattr(req, 'full_url') else str(req)
            if "plugin-a" in url:
                mock_resp.read.return_value = self._github_api_response("2.0.0")
            else:
                mock_resp.read.return_value = self._github_api_response("3.0.0")
            return mock_resp

        mock_urlopen.side_effect = side_effect

        result = check_outdated_plugins(cache, settings)
        assert len(result) == 1
        assert result[0]["plugin"] == "plugin-a"


class TestIntegration:
    """Test that findings appear in compute_pre_computed_findings output."""

    def _make_setup_profile(self):
        """Create a minimal setup profile stub."""
        class StubProfile:
            overlapping_triggers = []
            description_quality = []
        return StubProfile()

    def test_pre_computed_findings_includes_stale_cache(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "temp_git_999_xyz").mkdir()

        result = compute_pre_computed_findings(
            skills=[], agents=[], commands=[], sessions=[], missed=[],
            setup_profile=self._make_setup_profile(),
            plugins_cache=cache,
            settings_path=tmp_path / "settings.json",
        )

        assert "stale_cache" in result
        assert len(result["stale_cache"]) == 1
        assert result["stale_cache"][0]["type"] == "temp_leftover"
        assert result["counts"]["stale_cache"] == 1

    def test_pre_computed_findings_includes_outdated_plugins(self, tmp_path):
        result = compute_pre_computed_findings(
            skills=[], agents=[], commands=[], sessions=[], missed=[],
            setup_profile=self._make_setup_profile(),
            plugins_cache=tmp_path / "nonexistent",
            settings_path=tmp_path / "nonexistent.json",
        )

        assert "outdated_plugins" in result
        assert result["outdated_plugins"] == []
        assert result["counts"]["outdated_plugins"] == 0
