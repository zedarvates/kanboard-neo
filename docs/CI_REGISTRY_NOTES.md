# Container registry CI

The Docker workflow always publishes scheduled/tagged images to GitHub Container Registry (`ghcr.io`) using the repository-scoped `GITHUB_TOKEN`.

DockerHub and Quay publication are intentionally disabled until these repository secrets are configured:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `QUAY_USERNAME`
- `QUAY_TOKEN`

This prevents a missing external credential from blocking image builds and GHCR publication. When the external credentials are available, re-enable those registries as additional targets rather than replacing GHCR.
