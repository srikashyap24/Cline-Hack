# Slack AI Assistant Backend Architecture

This project provides a robust, production-ready backend for a Slack AI assistant designed to simplify technical text based on audience context. It uses an asynchronous MCP-style processing pipeline.

## Core Features Implemented

### 1. Slack Integration & Reliability
*   **Endpoint:** Exposes a POST `/slack/simplify` endpoint for Slash Commands.
*   **Timeouts:** Immediately responds with an ephemeral "Processing..." message to bypass Slack's strict 3-second timeout rule.
*   **Delayed Responses:** Orchestrates the heavy lifting asynchronously and posts the final results back using the provided `response_url`.
*   **Security:** Uses standard crypto to verify the `x-slack-signature` against a `SLACK_SIGNING_SECRET`, effectively preventing unauthorized payloads.

### 2. Processing Pipeline (MCP-style Services)
The processing is split into modular services orchestrated by `pipeline.js`:
1.  **Audience Detection (`audienceDetection.js`):** Analyzes the raw text to detect an intended audience (management, marketing, engineering, general) and categorizes whether the input is a new text or a refinement of a previous request.
2.  **Simplification Service (`simplification.js`):** Formats detailed prompts (using `response_format: { type: 'json_object' }`) instructing the LLM on specific tone rules according to the audience. Can also process follow-up instructions based on the prior state.
3.  **Accuracy Validation (`accuracyValidation.js`):** A secondary LLM pass compares the original text to the simplified output to ensure no critical facts or figures were lost. If validation fails, the pipeline automatically retries the simplification with a stricter prompt.

### 3. Iterative Refinement & State
*   **In-Memory Session Context (`sessionContext.js`):** Stores user sessions via a composite key (`userId:channelId`). If a user follows up with "make it shorter", the system detects this intent, retrieves the previous context, and passes it to the LLM to refine the existing output instead of starting over.
*   **In-Memory Cache:** Avoids repeated identical queries across different users by hashing the `core_text` and `audience` and returning the cached response if available.

### 4. Middleware & Foundations
*   **Express & Dotenv:** Built on Express.js with environment variables loaded from `.env`.
*   **Logging:** Centralized structured JSON logging via `winston` for easier debugging and monitoring.
*   **Error Handling:** A global error-handling middleware is in place, along with graceful fallback messages if the LLM or pipeline fails.

## Directory Structure
```text
src/
├── index.js                     # Express setup and middleware application
├── controllers/
│   └── slackController.js       # Handles incoming request mapping and delayed delivery
├── routes/
│   └── slack.js                 # Route definitions
├── services/
│   ├── accuracyValidation.js    # LLM validation layer
│   ├── audienceDetection.js     # LLM intent classification
│   ├── pipeline.js              # Pipeline orchestrator
│   ├── sessionContext.js        # Cache and session state
│   └── simplification.js        # Core rewriting logic
├── utils/
│   ├── logger.js                # Winston config
│   └── slackApi.js              # Axios wrapper for Slack
└── middleware/
    ├── errorHandler.js          # Global try/catch handler
    └── verifySlackSignature.js  # Slack webhook signature validation
```
