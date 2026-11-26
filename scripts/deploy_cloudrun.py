"""Deploy the backend to Google Cloud Run.

    gcloud auth login                                   # once
    .venv/Scripts/python scripts/deploy_cloudrun.py --project <project-id> --secrets
    .venv/Scripts/python scripts/deploy_cloudrun.py --project <project-id>   # later redeploys

Cloud Build builds the Dockerfile from the files .gcloudignore lets through
(Dockerfile, backend/, data/samples/), and Cloud Run serves it with:

- 1 GiB of memory: the backend holds about 630 MB once both spaCy models are
  loaded (measured 2026-11-22, Windows working set, login-es session);
- min 0 instances (free when idle; the first request after a pause waits for
  a cold start) and **max 1 instance**: the DeepSeek lock and the per-code
  budgets live in the process's memory, so one instance keeps them global;
- a 60-minute request timeout, the longest a WebSocket may stay open.

--secrets copies DEEPSEEK_API_KEY and MEDRA_DEPLOY_ACCESS_CODES from the local
.env into Secret Manager (piped through stdin: never printed, never in argv or
a file) and lets the service read them; the service sees the codes as
MEDRA_ACCESS_CODES. (A different name in .env, so the local backend does not
start asking for codes.) Run it again after changing either.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
# service env var -> (Secret Manager name, key in the local .env)
SECRETS = {
    "DEEPSEEK_API_KEY": ("medra-deepseek-key", "DEEPSEEK_API_KEY"),
    "MEDRA_ACCESS_CODES": ("medra-access-codes", "MEDRA_DEPLOY_ACCESS_CODES"),
}
APIS = ["run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com", "secretmanager.googleapis.com"]

GCLOUD = shutil.which("gcloud") or shutil.which("gcloud.cmd")


def gcloud(*args: str, project: str, stdin: str | None = None, check: bool = True, capture: bool = False) -> str:
    cmd = [GCLOUD, *args, f"--project={project}", "--quiet"]
    print("$ gcloud " + " ".join(args))  # arguments never contain a secret
    result = subprocess.run(cmd, input=stdin, text=True, capture_output=capture or stdin is not None, cwd=ROOT)
    if check and result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(f"gcloud failed ({result.returncode})")
    return (result.stdout or "").strip() if result.returncode == 0 else ""


def compute_account(project: str) -> str:
    """The project's default compute service account: Cloud Build builds and Cloud Run runs as it."""
    number = gcloud("projects", "describe", project, "--format=value(projectNumber)", project=project, capture=True)
    return f"{number}-compute@developer.gserviceaccount.com"


def allow_builds(project: str) -> None:
    # New projects no longer give this account build rights by default; run.builder is the
    # role Google documents for source deploys (logs, Artifact Registry, service usage).
    # Without serviceUsageConsumer the first deploy fails. Grants can take a minute or two
    # to apply, so a retry may be needed.
    member = f"--member=serviceAccount:{compute_account(project)}"
    for role in ("roles/run.builder", "roles/serviceusage.serviceUsageConsumer"):
        gcloud("projects", "add-iam-policy-binding", project, member, f"--role={role}", "--condition=None",
               project=project, capture=True)


def push_secrets(project: str) -> None:
    env = dotenv_values(ROOT / ".env")
    runtime_account = compute_account(project)  # Cloud Run's default identity
    for name, key in SECRETS.values():
        value = (env.get(key) or "").strip()
        if not value:
            sys.exit(f"{key} is empty in .env: set it there first")
        exists = gcloud("secrets", "describe", name, "--format=value(name)", project=project, check=False, capture=True)
        if exists:
            gcloud("secrets", "versions", "add", name, "--data-file=-", project=project, stdin=value)
        else:
            gcloud("secrets", "create", name, "--replication-policy=automatic", "--data-file=-", project=project, stdin=value)
        gcloud("secrets", "add-iam-policy-binding", name, f"--member=serviceAccount:{runtime_account}",
               "--role=roles/secretmanager.secretAccessor", project=project, capture=True)
        print(f"  {key} -> secret {name} (value not shown)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True, help="Google Cloud project id")
    parser.add_argument("--region", default="europe-west1", help="Cloud Run region (default: Belgium)")
    parser.add_argument("--service", default="medra")
    parser.add_argument("--origin", default="https://joejbaldwin.github.io", help="dashboard origin allowed by CORS")
    parser.add_argument("--secrets", action="store_true", help="copy the key and access codes from .env first")
    args = parser.parse_args()
    if not GCLOUD:
        sys.exit("gcloud not found: install the Google Cloud CLI first")

    gcloud("services", "enable", *APIS, project=args.project)
    allow_builds(args.project)
    if args.secrets:
        push_secrets(args.project)
    gcloud(
        "run", "deploy", args.service, "--source=.", f"--region={args.region}",
        "--allow-unauthenticated", "--memory=1Gi", "--cpu=1",
        "--min-instances=0", "--max-instances=1", "--timeout=3600", "--concurrency=20",
        f"--set-env-vars=MEDRA_ALLOWED_ORIGINS={args.origin}",
        "--set-secrets=" + ",".join(f"{var}={name}:latest" for var, (name, _) in SECRETS.items()),
        project=args.project,
    )
    url = gcloud("run", "services", "describe", args.service, f"--region={args.region}", "--format=value(status.url)",
                 project=args.project, capture=True)
    print(f"\nBackend: {url}\nSet the GitHub repository variable MEDRA_BACKEND_URL to that URL.")


if __name__ == "__main__":
    main()
