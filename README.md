# HelpMate AI

A small, grounded customer-support chatbot starter. It includes a FastAPI API, a browser chat page, an editable FAQ knowledge base, a Docker image, Kubernetes manifests, and a GitHub Actions workflow that tests, pushes to Azure Container Registry (ACR), and deploys to Azure Kubernetes Service (AKS).

The sample FAQ is for a fictional online store. Replace [`app/knowledge_base.json`](app/knowledge_base.json) with approved answers for your own business before using the app with customers. The assistant is instructed to stay within those answers and hand off questions it cannot answer.

## Run locally

Requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
export AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE.openai.azure.com"
export AZURE_OPENAI_API_KEY="YOUR-KEY"
export AZURE_OPENAI_DEPLOYMENT="YOUR-MODEL-DEPLOYMENT"
export AZURE_OPENAI_API_VERSION="2024-10-21"
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. The API is documented at <http://localhost:8000/docs>; its health endpoint is <http://localhost:8000/healthz>. Run tests without Azure credentials using `python -m pytest -q`.

## Build and run with Docker

```bash
docker build -t helpmate-api:local .
docker run --rm -p 8000:8000 \
  -e AZURE_OPENAI_ENDPOINT \
  -e AZURE_OPENAI_API_KEY \
  -e AZURE_OPENAI_DEPLOYMENT \
  -e AZURE_OPENAI_API_VERSION \
  helpmate-api:local
```

## Azure and GitHub Actions setup

Create an Azure OpenAI resource and deploy a chat model. Note its resource endpoint, API key, and **deployment name** (the deployment name is not necessarily the model name). Create an ACR and AKS cluster in your Azure subscription. Configure AKS to pull from ACR (for example, attach the registry with `az aks update --resource-group <resource-group> --name <cluster-name> --attach-acr <acr-name>`).

Set up GitHub-to-Azure workload identity federation for this repository and its `main` branch; do not use a long-lived Azure client secret. Grant the federated identity access to push to the ACR and the required AKS cluster-user/deployment permissions. The identity also needs permission to retrieve AKS credentials. Ensure the AKS nodes can pull from the ACR.

In the repository, configure these **Actions variables**:

| Variable | Value |
|---|---|
| `AZURE_CLIENT_ID` | Client ID of the federated Microsoft Entra application or user-assigned identity |
| `AZURE_TENANT_ID` | Microsoft Entra tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `ACR_NAME` | ACR resource name, without `.azurecr.io` |
| `AKS_RESOURCE_GROUP` | Resource group containing the AKS cluster |
| `AKS_CLUSTER_NAME` | AKS cluster name |
| `AZURE_OPENAI_DEPLOYMENT` | Azure OpenAI model deployment name |
| `AZURE_OPENAI_API_VERSION` | API version; defaults to `2024-10-21` if omitted |

Configure these **Actions secrets**:

| Secret | Value |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |

The workflow in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) runs tests on each push to `main`, builds and pushes an image tagged with the commit SHA, updates the Kubernetes secret, and rolls out the deployment. It can also be started manually from the Actions tab. The first run creates a public Azure LoadBalancer service; retrieve its address with:

```bash
kubectl get service helpmate-service
```

Restrict access and configure HTTPS, a domain, and ingress before exposing this starter to real customers. The sample has no user authentication, conversation persistence, or private-data access; add and review those deliberately before production use.
