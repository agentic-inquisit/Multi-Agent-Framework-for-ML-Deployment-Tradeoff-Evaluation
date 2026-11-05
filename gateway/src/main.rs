//! Public-facing edge in front of the internal-only Python/LangGraph worker.
//! Owns auth, request validation, and rate limiting; the worker owns graph
//! execution. See README.md for the full pipeline/deployment diagrams.

use axum::{
    extract::{Path, State},
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::{env, sync::Arc};

#[derive(Clone)]
struct AppState {
    http: reqwest::Client,
    worker_url: String,
    api_key: String,
}

#[derive(Deserialize)]
struct DecisionBrief {
    decision_name: String,
    one_liner: String,
    problem: String,
    capability: String,
    current_approach: String,
    #[serde(default)]
    candidate_approaches: Vec<String>,
    deployment_target: String,
    hardware_constraints: String,
    latency_budget: String,
    compliance_constraints: String,
    team_context: String,
    budget_ceiling: String,
    success_metric: String,
}

impl DecisionBrief {
    /// Mirrors worker/src/state.py::DecisionBrief required-field check —
    /// reject an incomplete brief here so the worker (and an LLM call)
    /// never sees it.
    fn missing_fields(&self) -> Vec<&'static str> {
        let mut missing = Vec::new();
        let required: [(&str, &str); 12] = [
            ("decision_name", &self.decision_name),
            ("one_liner", &self.one_liner),
            ("problem", &self.problem),
            ("capability", &self.capability),
            ("current_approach", &self.current_approach),
            ("deployment_target", &self.deployment_target),
            ("hardware_constraints", &self.hardware_constraints),
            ("latency_budget", &self.latency_budget),
            ("compliance_constraints", &self.compliance_constraints),
            ("team_context", &self.team_context),
            ("budget_ceiling", &self.budget_ceiling),
            ("success_metric", &self.success_metric),
        ];
        for (field, value) in required {
            if value.trim().is_empty() {
                missing.push(field);
            }
        }
        missing
    }
}

#[derive(Serialize)]
struct ErrorBody {
    error: String,
    missing_fields: Vec<&'static str>,
}

fn authorized(headers: &HeaderMap, expected_key: &str) -> bool {
    headers
        .get("x-api-key")
        .and_then(|v| v.to_str().ok())
        .is_some_and(|key| key == expected_key)
}

async fn healthz() -> &'static str {
    "ok"
}

async fn create_run(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    Json(brief): Json<DecisionBrief>,
) -> impl IntoResponse {
    if !authorized(&headers, &state.api_key) {
        return (StatusCode::UNAUTHORIZED, "invalid api key").into_response();
    }

    let missing = brief.missing_fields();
    if !missing.is_empty() {
        return (
            StatusCode::UNPROCESSABLE_ENTITY,
            Json(ErrorBody {
                error: "decision_brief is incomplete".into(),
                missing_fields: missing,
            }),
        )
            .into_response();
    }

    proxy_json(&state, reqwest::Method::POST, "/runs", Some(&brief)).await
}

async fn get_run(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    Path(thread_id): Path<String>,
) -> impl IntoResponse {
    if !authorized(&headers, &state.api_key) {
        return (StatusCode::UNAUTHORIZED, "invalid api key").into_response();
    }
    proxy_json::<()>(&state, reqwest::Method::GET, &format!("/runs/{thread_id}"), None).await
}

async fn resume_run(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    Path(thread_id): Path<String>,
    body: Json<serde_json::Value>,
) -> impl IntoResponse {
    if !authorized(&headers, &state.api_key) {
        return (StatusCode::UNAUTHORIZED, "invalid api key").into_response();
    }
    proxy_json(
        &state,
        reqwest::Method::POST,
        &format!("/runs/{thread_id}/resume"),
        Some(&body.0),
    )
    .await
}

async fn trigger_monitor(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    Path(thread_id): Path<String>,
) -> impl IntoResponse {
    if !authorized(&headers, &state.api_key) {
        return (StatusCode::UNAUTHORIZED, "invalid api key").into_response();
    }
    proxy_json::<()>(
        &state,
        reqwest::Method::POST,
        &format!("/monitor/{thread_id}/run"),
        None,
    )
    .await
}

async fn proxy_json<B: Serialize + ?Sized>(
    state: &AppState,
    method: reqwest::Method,
    path: &str,
    body: Option<&B>,
) -> axum::response::Response {
    let url = format!("{}{}", state.worker_url, path);
    let mut req = state.http.request(method, url);
    if let Some(body) = body {
        req = req.json(body);
    }

    match req.send().await {
        Ok(resp) => {
            let status = StatusCode::from_u16(resp.status().as_u16()).unwrap_or(StatusCode::BAD_GATEWAY);
            match resp.json::<serde_json::Value>().await {
                Ok(json) => (status, Json(json)).into_response(),
                Err(_) => (StatusCode::BAD_GATEWAY, "worker returned a non-JSON response").into_response(),
            }
        }
        Err(_) => (StatusCode::BAD_GATEWAY, "worker unreachable").into_response(),
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let state = Arc::new(AppState {
        http: reqwest::Client::new(),
        worker_url: env::var("WORKER_URL").unwrap_or_else(|_| "http://worker:8000".into()),
        api_key: env::var("GATEWAY_API_KEY").expect("GATEWAY_API_KEY must be set"),
    });

    let app = Router::new()
        .route("/healthz", get(healthz))
        .route("/runs", post(create_run))
        .route("/runs/:thread_id", get(get_run))
        .route("/runs/:thread_id/resume", post(resume_run))
        .route("/monitor/:thread_id/run", post(trigger_monitor))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    tracing::info!("gateway listening on :8080");
    axum::serve(listener, app).await.unwrap();
}
