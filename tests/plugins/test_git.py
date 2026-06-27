import os
import subprocess
import time
from unittest.mock import Mock, call, patch
import plugins.git as git_module


def git_result(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["git"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class TestGit:
    def setup_method(self):
        self.master_mock = Mock()
        self.master_mock.transID = 481031730
        self.git = git_module.git("SID", self.master_mock)

    def test_background(self, tmp_path):
        lock_path = tmp_path / ".kassa-git.lock"
        with patch.object(git_module, "KASSA_GIT_LOCK", str(lock_path)), patch.object(
            self.git, "_commit"
        ) as mock_commit, patch("plugins.git.fcntl.flock") as mock_flock:
            self.git.background()

        mock_commit.assert_called_once_with()
        mock_flock.assert_has_calls(
            [
                call(mock_flock.call_args_list[0].args[0], git_module.fcntl.LOCK_EX),
                call(mock_flock.call_args_list[0].args[0], git_module.fcntl.LOCK_UN),
            ]
        )

    def test_commit_adds_and_commits_data_repo(self):
        with patch("plugins.git.subprocess.run", return_value=git_result()) as mock_run:
            self.git._commit()

        assert mock_run.call_args_list == [
            call(
                ["git", "add", "-A", "."],
                cwd="data",
                check=False,
                capture_output=True,
                text=True,
            ),
            call(
                ["git", "commit", "-m", "481031730", "."],
                cwd="data",
                check=False,
                capture_output=True,
                text=True,
            ),
        ]

    def test_commit_removes_stale_index_lock_and_retries(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        index_lock = git_dir / "index.lock"
        index_lock.write_text("", encoding="utf-8")
        old_timestamp = time.time() - git_module.STALE_INDEX_LOCK_SECONDS - 1
        os.utime(index_lock, (old_timestamp, old_timestamp))
        index_lock_error = git_result(
            returncode=128,
            stderr="fatal: Unable to create 'data/.git/index.lock': File exists.",
        )

        with patch.object(git_module, "DATA_REPO", str(tmp_path)), patch.object(
            git_module, "GIT_INDEX_LOCK", str(index_lock)
        ), patch(
            "plugins.git.subprocess.run",
            side_effect=[git_result(), index_lock_error, git_result(), git_result()],
        ) as mock_run:
            self.git._commit()

        assert not index_lock.exists()
        assert mock_run.call_count == 4

    def test_commit_keeps_recent_index_lock(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        index_lock = git_dir / "index.lock"
        index_lock.write_text("", encoding="utf-8")
        index_lock_error = git_result(
            returncode=128,
            stderr="fatal: Unable to create 'data/.git/index.lock': File exists.",
        )

        with patch.object(git_module, "DATA_REPO", str(tmp_path)), patch.object(
            git_module, "GIT_INDEX_LOCK", str(index_lock)
        ), patch(
            "plugins.git.subprocess.run", side_effect=[git_result(), index_lock_error]
        ):
            self.git._commit()

        assert index_lock.exists()

    def test_remove_stale_index_lock_missing_file(self, tmp_path):
        with patch.object(git_module, "GIT_INDEX_LOCK", str(tmp_path / "index.lock")):
            assert self.git._remove_stale_index_lock() is False

    def test_remove_stale_index_lock_disappears_before_unlink(self, tmp_path):
        index_lock = tmp_path / "index.lock"
        index_lock.write_text("", encoding="utf-8")
        old_timestamp = time.time() - git_module.STALE_INDEX_LOCK_SECONDS - 1
        os.utime(index_lock, (old_timestamp, old_timestamp))

        with patch.object(git_module, "GIT_INDEX_LOCK", str(index_lock)), patch(
            "plugins.git.os.unlink", side_effect=FileNotFoundError
        ):
            assert self.git._remove_stale_index_lock() is False

    def test_remove_stale_index_lock_logs_unlink_errors(self, tmp_path, caplog):
        index_lock = tmp_path / "index.lock"
        index_lock.write_text("", encoding="utf-8")
        old_timestamp = time.time() - git_module.STALE_INDEX_LOCK_SECONDS - 1
        os.utime(index_lock, (old_timestamp, old_timestamp))

        with patch.object(git_module, "GIT_INDEX_LOCK", str(index_lock)), patch(
            "plugins.git.os.unlink", side_effect=OSError("busy")
        ):
            assert self.git._remove_stale_index_lock() is False

        assert "data_git_index_lock_remove_failed sid=SID" in caplog.text

    def test_background_uses_shared_lock(self):
        other = git_module.git("SID2", Mock())

        assert self.git.lock is other.lock

    def test_hook_post_checkout(self):
        with patch("plugins.git.threading.Thread") as mock_thread:
            self.git.hook_post_checkout(None)
            mock_thread.assert_called()

    def test_input(self):
        # Since input method passes, just call it to ensure coverage
        self.git.input("any_text")

    def test_startup(self):
        # Since startup method passes, just call it to ensure coverage
        self.git.startup()
