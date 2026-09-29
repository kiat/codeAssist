# Gemini Over Vertex AI Setup

Gemini over Vertex AI lets CodeAssist use Gemini models through Google Cloud.
Unlike the Gemini Developer API provider, Vertex credentials are deployment-level
server configuration. Instructors should not paste Vertex credentials into a
course or assignment.

## Supported Auth Modes

### Vertex AI Express / API Key

Use this for a server-managed Vertex-compatible API key:

```bash
VERTEX_AI_AUTH_MODE=api_key
VERTEX_AI_API_KEY=<vertex-api-key>
GOOGLE_CLOUD_LOCATION=global
```

`GOOGLE_CLOUD_PROJECT` is optional in API-key mode. If it is set, CodeAssist
passes both project and location to the Vertex client.

### Standard Vertex AI / ADC

Use this for a service account or another Application Default Credentials setup:

```bash
GOOGLE_CLOUD_PROJECT=<project-id-or-number>
GOOGLE_CLOUD_LOCATION=global
GOOGLE_APPLICATION_CREDENTIALS=/path/in/container/service-account.json
```

Leave `VERTEX_AI_AUTH_MODE` unset for ADC mode.

## Google Cloud Requirements

The Google Cloud project must have the Vertex AI API enabled.

The configured identity, API key project, or service account must be able to call
Vertex prediction APIs. The required permission is:

```text
aiplatform.endpoints.predict
```

Use a role that includes that permission, such as Vertex AI Express User for
Express/API-key mode or Vertex AI User for standard Vertex AI service-account
mode.

## Local Docker Setup

After changing dependencies or Vertex env vars, rebuild the backend container:

```bash
docker compose down
docker compose up -d --build db backend
docker compose exec backend flask db upgrade
```

Confirm the Google Gen AI SDK is installed inside the backend image:

```bash
docker compose exec backend python -c "from google import genai; print('google-genai import ok')"
```

## Manual UI Test

1. Open Course AI Settings.
2. Select `Gemini over Vertex AI`.
3. Click `Refresh Models`.
4. Select `gemini-2.5-flash`.
5. Click `Test Selected Model`.

If the test returns `PROVIDER_PERMISSION_ERROR`, CodeAssist reached Google Cloud
but the project or key does not have `aiplatform.endpoints.predict`.
