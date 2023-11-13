import os


def main():
    maven_command = "./mvnw " + os.environ["MAVEN_GOAL"]
    default_args = os.getenv("DEFAULT_ARGUMENTS")
    extra_args = os.getenv("EXTRA_ARGUMENTS") or os.getenv("MAVEN_EXTRA_ARGUMENTS")

    if default_args:
        maven_command += " " + default_args

    if extra_args:
        maven_command += " " + extra_args

    if "true" in [os.getenv("IS_MAIN_BRANCH"), os.getenv("IS_RELEASE_BRANCH")]:
        maven_command += " -Dbuild.release"

    if os.getenv("IS_RELEASE_CANDIDATE_BRANCH") == "true":
        maven_command += " -Dbuild.candidate"

    print(maven_command, flush=True)
    os.system(maven_command)


if __name__ == "__main__":
    main()
