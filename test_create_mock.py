import os
import yaml
import trigger_deployment
import pytest
from pathlib import Path


class TestTriggerDeployment:

    @pytest.fixture(autouse=True)
    def setup_fixtures(self, monkeypatch, capsys, tmp_path):
        self.monkeypatch = monkeypatch
        self.capsys = capsys
        self.tmp_path = tmp_path

    @pytest.fixture(autouse=True)
    def setup_vars(self, monkeypatch, tmp_path):
        """
        Setup variables for all tests
        """
        trigger_deployment_yaml = f"""
            repository: "terragrunt-applications"
            environment: "sandbox//sandbox"
        """

        monkeypatch.setenv("DEPLOYMENT_TYPE", "applications")
        monkeypatch.setenv("TRIGGER_DEPLOYMENT", trigger_deployment_yaml)
        monkeypatch.setenv("REPOSITORY_NAME", "system-team-maven-demo")
        monkeypatch.setenv("RELEASED_VERSION", "1.0.5")
        monkeypatch.setenv("BRANCH_NAME", "master")
        monkeypatch.setenv("GITHUB_APP_OWNER", "Towner")
        monkeypatch.setenv("GH_TOKEN", "TOKEN")
        monkeypatch.setenv("TMP_PATH", str(tmp_path))

        monkeypatch.setattr("subprocess.run", mock_subprocess_run)
        monkeypatch.setattr('os.getcwd', mock_getcwd)

    def test_deployment_type_is_missing(self):
        self.monkeypatch.delenv("DEPLOYMENT_TYPE")

        with pytest.raises(KeyError) as exception_info:
            trigger_deployment.main()

        assert "DEPLOYMENT_TYPE" in str(exception_info.value)

    def test_deployment_type_is_invalid(self):
        self.monkeypatch.setenv("DEPLOYMENT_TYPE", "invalid")

        with pytest.raises(Exception) as exception_info:
            trigger_deployment.main()

        assert "Invalid deployment type invalid" in str(exception_info.value)

    def test_trigger_deployment_is_missing(self):
        self.monkeypatch.delenv("TRIGGER_DEPLOYMENT")

        with pytest.raises(KeyError) as exception_info:
            trigger_deployment.main()

        assert "TRIGGER_DEPLOYMENT" in str(exception_info.value)

    def test_trigger_deployment_is_invalid_yaml(self):
        self.monkeypatch.setenv("TRIGGER_DEPLOYMENT", "key : {} []")

        with pytest.raises(yaml.YAMLError):
            trigger_deployment.main()

    def test_trigger_deployment_is_invalid_type(self):
        self.monkeypatch.setenv("TRIGGER_DEPLOYMENT", "")

        with pytest.raises(Exception) as exception_info:
            trigger_deployment.main()

        assert "Error parsing invalid YAML for 'trigger-deployment' input" in str(exception_info.value)

    def test_trigger_deployment_missing_repository(self):
        self.monkeypatch.setenv("TRIGGER_DEPLOYMENT", "environment: sandbox/applications/sandbox")

        with pytest.raises(ValueError) as exception_info:
            trigger_deployment.main()

        assert "The keys 'repository' and 'environment' are required for the 'trigger-deployment' input" in str(
            exception_info.value)

    def test_trigger_deployment_missing_environment(self):
        self.monkeypatch.setenv("TRIGGER_DEPLOYMENT", "repository: terragrunt-applications")

        with pytest.raises(ValueError) as exception_info:
            trigger_deployment.main()

        assert "The keys 'repository' and 'environment' are required for the 'trigger-deployment' input" in str(
            exception_info.value)

    def test_trigger_deployment_missing_released_version(self):
        self.monkeypatch.delenv("RELEASED_VERSION")

        with pytest.raises(ValueError) as exception_info:
            trigger_deployment.main()

        assert "Released version is required" in str(exception_info.value)

    def test_trigger_deployment_missing_branch_pattern(self):
        trigger_deployment_yaml = """
            branch_pattern: release/.*
            repository: terragrunt-applications
            environment: sandbox/applications/sandbox     
        """
        self.monkeypatch.setenv("TRIGGER_DEPLOYMENT", trigger_deployment_yaml)

        trigger_deployment.main()

        assert "does not match the configured branch pattern of release/.*" in self.capsys.readouterr().out

    def test_git_checkout_success(self):
        trigger_deployment.git_checkout("terragrunt-applications")

        capture = self.capsys.readouterr().out

        assert "git clone" in capture
        assert "https://x-access-token:TOKEN@github.com/Org/terragrunt-applications.git" in capture
        assert "--depth 1" in capture

    def test_git_checkout_app_owner_missing(self):
        self.monkeypatch.delenv("GITHUB_APP_OWNER")

        with pytest.raises(KeyError) as exception_info:
            trigger_deployment.git_checkout("terragrunt-applications")

        assert "GITHUB_APP_OWNER" in str(exception_info.value)

    def test_git_checkout_gh_token_missing(self):
        self.monkeypatch.delenv("GH_TOKEN")

        with pytest.raises(KeyError) as exception_info:
            trigger_deployment.git_checkout("terragrunt-applications")

        assert "GH_TOKEN" in str(exception_info.value)

    def test_invalid_applications_yaml(self):
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_broken_yaml)

        with pytest.raises(yaml.YAMLError):
            trigger_deployment.main()

        assert "Error parsing YAML file" in self.capsys.readouterr().out

    def test_deployment_type_key_is_not_found(self):
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_wrong_key)

        trigger_deployment.main()

        assert "It does not contain the key 'applications'" in self.capsys.readouterr().out

    def test_application_not_found_in_yaml(self):
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_correct_yaml)
        self.monkeypatch.setenv("REPOSITORY_NAME", "invalid-repository-demo")

        trigger_deployment.main()

        assert "Repository 'invalid-repository-demo' not found in" in self.capsys.readouterr().out

    def test_released_version_matches_current(self):
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_correct_yaml)
        self.monkeypatch.setenv("RELEASED_VERSION", "1.0.3")

        trigger_deployment.main()

        assert "Released version 1.0.3 matches the value defined" in self.capsys.readouterr().out

    def test_skip_version_bump(self):
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_skip_bump)

        trigger_deployment.main()

        assert "No version has been modified" in self.capsys.readouterr().out

    def test_released_version_updated_correctly(self):
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_correct_yaml)

        trigger_deployment.main()

        deployment_repository_path = self.tmp_path / "terragrunt-ations"
        assert not deployment_repository_path.exists()

        capture = self.capsys.readouterr().out

        assert 'Version 1.0.5 updated in' in capture
        assert 'git config user.name ""' in capture
        assert 'git config user.email "github-actions"' in capture
        assert 'git add sandbox///applications.yaml' in capture
        assert 'git commit -m Update --maven-demo to version 1.0.5 on #sandbox' in capture
        assert 'git push --set-upstream origin HEAD:master' in capture

    def test_charts_are_update_correctly(self):
        self.monkeypatch.setenv("DEPLOYMENT_TYPE", "charts")
        self.monkeypatch.setenv("REPOSITORY_NAME", "-base-chart")
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_charts_yaml)

        trigger_deployment.main()

        deployment_repository_path = self.tmp_path / "terragrunt--applications"
        assert not deployment_repository_path.exists()

        capture = self.capsys.readouterr().out

        assert 'Version 1.0.5 updated in' in capture
        assert 'git config user.name "github-actions"' in capture
        assert 'git config user.email "github-actions@.com"' in capture
        assert 'git add sandbox///charts.yaml' in capture
        assert 'git commit -m Update -base-chart to version 1.0.5 on #' in capture
        assert 'git push --set-upstream origin HEAD:master' in capture

    def test_git_push_exhaust_retries(self):
        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_correct_yaml)
        self.monkeypatch.setattr("trigger_deployment.commit_and_push", mock_git_push_exception)

        with pytest.raises(trigger_deployment.GitPushException):
            trigger_deployment.main()

        capture = self.capsys.readouterr().out

        assert "Git push failed on attempt 1/3" in capture
        assert "Git push failed on attempt 2/3" in capture
        assert "Git push failed on attempt 3/3" in capture

    def test_git_push_success_after_two_retries(self):
        self.attempt = 1

        def mock_git_push_retry(file_path, commit_message):
            if self.attempt <= 2:
                self.attempt += 1
                raise trigger_deployment.GitPushException

        self.monkeypatch.setattr("trigger_deployment.git_checkout", mock_checkout_correct_yaml)
        self.monkeypatch.setattr("trigger_deployment.commit_and_push", mock_git_push_retry)

        trigger_deployment.main()

        capture = self.capsys.readouterr().out

        assert "Git push failed on attempt 1/3" in capture
        assert "Git push failed on attempt 2/3" in capture
        assert "Git push failed on attempt 3/3" not in capture


def mock_subprocess_run(command, check):
    print(" ".join(command))


def mock_getcwd():
    tmp_path = os.environ['TMP_PATH']
    os.chdir(tmp_path)
    return tmp_path


def mock_git_push_exception(file_path, commit_message):
    raise trigger_deployment.GitPushException


def mock_checkout_correct_yaml(repository):
    create_directory_structure("""
        applications:
          ---demo:
            version: 1.0.3
    """)


def mock_checkout_charts_yaml(repository):
    create_directory_structure("""
        charts:
          -base-chart:
            version: 1.0.4
    """)


def mock_checkout_skip_bump(repository):
    create_directory_structure("""
        applications:
          system---demo:
            version: 1.0.3
            skip_auto_version_bump: true
    """)


def mock_checkout_broken_yaml(repository):
    create_directory_structure("""
        applications: [] {}
    """)


def mock_checkout_wrong_key(repository):
    create_directory_structure("""
        invalid: {}
    """)


def create_directory_structure(yaml_content):
    trigger_deployment_yaml = os.environ['TRIGGER_DEPLOYMENT']
    parsed_trigger = yaml.safe_load(trigger_deployment_yaml)

    tmp_path = Path(os.environ['TMP_PATH'])
    environment_path = tmp_path / parsed_trigger['repository'] / parsed_trigger['environment']
    os.makedirs(environment_path, exist_ok=True)
    yaml_file_name = f"{os.environ['DEPLOYMENT_TYPE']}.yaml"

    with open(environment_path / yaml_file_name, 'w') as yaml_file:
        yaml_file.write(yaml_content)
