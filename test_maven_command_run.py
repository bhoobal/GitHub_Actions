import maven_command_run
import pytest


def mock_system_command(command):
    print(command)


class TestMavenCommandRun:

    @pytest.fixture(autouse=True)
    def setup_fixtures(self, monkeypatch, capsys):
        self.monkeypatch = monkeypatch
        self.capsys = capsys
        monkeypatch.setattr("os.system", mock_system_command)

    def test_simple_goal(self):
        """
        Test with a simple Maven goal
        """

        self.monkeypatch.setenv("MAVEN_GOAL", "verify")

        maven_command_run.main()

        assert "./mvnw verify" in self.capsys.readouterr().out

    def test_with_default_arguments(self):
        """
        Test with Maven goal with default arguments
        """

        self.monkeypatch.setenv("MAVEN_GOAL", "package")
        self.monkeypatch.setenv("DEFAULT_ARGUMENTS", "--info")

        maven_command_run.main()

        assert "./mvnw package --info" in self.capsys.readouterr().out

    def test_with_extra_arguments(self):
        """
        Test with Maven goal with extra arguments
        """

        self.monkeypatch.setenv("MAVEN_GOAL", "install")
        self.monkeypatch.setenv("MAVEN_EXTRA_ARGUMENTS", "--info")

        maven_command_run.main()

        assert "./mvnw install --info" in self.capsys.readouterr().out

        self.monkeypatch.setenv("EXTRA_ARGUMENTS", "--stacktrace")

        maven_command_run.main()

        assert "./mvnw install --stacktrace" in self.capsys.readouterr().out

    def test_on_main_branch(self):
        """
        Test with Maven goal on main branch
        """

        self.monkeypatch.setenv("MAVEN_GOAL", "test")
        self.monkeypatch.setenv("IS_MAIN_BRANCH", "true")

        maven_command_run.main()

        assert "./mvnw test -Dbuild.release" in self.capsys.readouterr().out

    def test_on_release_branch(self):
        """
        Test with Maven goal on release branch
        """

        self.monkeypatch.setenv("MAVEN_GOAL", "test")
        self.monkeypatch.setenv("IS_RELEASE_BRANCH", "true")

        maven_command_run.main()

        assert "./mvnw test -Dbuild.release" in self.capsys.readouterr().out

    def test_on_release_candidate_branch(self):
        """
        Test with Maven goal on release candidate branch
        """

        self.monkeypatch.setenv("MAVEN_GOAL", "test")
        self.monkeypatch.setenv("IS_RELEASE_CANDIDATE_BRANCH", "true")

        maven_command_run.main()

        assert "./mvnw test -Dbuild.candidate" in self.capsys.readouterr().out

    def test_with_all_options(self):
        """
        Test with Maven goal with default and extra arguments on a main branch
        """

        self.monkeypatch.setenv("MAVEN_GOAL", "test")
        self.monkeypatch.setenv("DEFAULT_ARGUMENTS", "--batch-mode --update-snapshots -Dstyle.color=always")
        self.monkeypatch.setenv("MAVEN_EXTRA_ARGUMENTS", "--info")
        self.monkeypatch.setenv("IS_MAIN_BRANCH", "true")

        maven_command_run.main()

        assert "./mvnw test --batch-mode --update-snapshots -Dstyle.color=always --info -Dbuild.release" \
               in self.capsys.readouterr().out
