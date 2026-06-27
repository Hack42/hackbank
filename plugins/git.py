# -*- coding: utf-8 -*-
import fcntl
import logging
import os
import subprocess
import threading
import time

logger = logging.getLogger(__name__)

DATA_REPO = "data"
KASSA_GIT_LOCK = os.path.join(DATA_REPO, ".kassa-git.lock")
GIT_INDEX_LOCK = os.path.join(DATA_REPO, ".git", "index.lock")
STALE_INDEX_LOCK_SECONDS = 60


class git:
    lock = threading.Lock()

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def _run_git(self, args):
        return subprocess.run(
            ["git", *args],
            cwd=DATA_REPO,
            check=False,
            capture_output=True,
            text=True,
        )

    def _remove_stale_index_lock(self):
        try:
            age = time.time() - os.path.getmtime(GIT_INDEX_LOCK)
        except FileNotFoundError:
            return False

        if age < STALE_INDEX_LOCK_SECONDS:
            logger.warning(
                "data_git_index_lock_present sid=%s age_seconds=%.1f",
                self.SID,
                age,
            )
            return False

        try:
            os.unlink(GIT_INDEX_LOCK)
        except FileNotFoundError:
            return False
        except OSError:
            logger.exception("data_git_index_lock_remove_failed sid=%s", self.SID)
            return False

        logger.warning(
            "data_git_index_lock_removed sid=%s age_seconds=%.1f",
            self.SID,
            age,
        )
        return True

    def _commit(self):
        add_result = self._run_git(["add", "-A", "."])
        commit_result = self._run_git(["commit", "-m", str(self.master.transID), "."])
        combined_output = (add_result.stderr or "") + (commit_result.stderr or "")

        if "index.lock" in combined_output and self._remove_stale_index_lock():
            add_result = self._run_git(["add", "-A", "."])
            commit_result = self._run_git(
                ["commit", "-m", str(self.master.transID), "."]
            )

        if add_result.returncode != 0 or commit_result.returncode != 0:
            message = "\n".join(
                part
                for part in (
                    add_result.stderr.strip(),
                    commit_result.stderr.strip(),
                    commit_result.stdout.strip(),
                )
                if part
            )
            if "nothing to commit" not in message:
                logger.warning(
                    "data_git_commit_failed sid=%s error=%s", self.SID, message
                )

    def background(self):
        with self.lock:
            with open(KASSA_GIT_LOCK, "w", encoding="utf-8") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
                try:
                    self._commit()
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

    def hook_post_checkout(self, _text):
        threading.Thread(target=self.background).start()

    def input(self, text):
        pass

    def startup(self):
        pass
