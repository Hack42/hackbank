from unittest.mock import Mock, patch
import plugins.git as git_module
import threading


class TestGit:
    def setup_method(self):
        self.master_mock = Mock()
        self.git = git_module.git("SID", self.master_mock)

    def test_background(self):
        with patch('plugins.git.os.system') as mock_system:
            self.git.background()
            mock_system.assert_called_with("cd data && git commit -m " + str(self.master_mock.transID) + " .")

    def test_hook_post_checkout(self):
        with patch('plugins.git.threading.Thread') as mock_thread:
            self.git.hook_post_checkout(None)
            mock_thread.assert_called()

    def test_input(self):
        # Since input method passes, just call it to ensure coverage
        self.git.input("any_text")

    def test_startup(self):
        # Since startup method passes, just call it to ensure coverage
        self.git.startup()

