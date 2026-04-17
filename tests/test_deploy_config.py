"""Tests for the Vertex deploy config builder.

The goal: importing ``nova_adk_agent.deploy.vertex`` must NEVER talk to GCP,
and the config builder must fail loudly when required env vars are missing.
"""
import os

import pytest


def test_deploy_module_import_is_side_effect_free():
    # Just importing should not raise, even with no env set.
    import nova_adk_agent.deploy.vertex as v

    assert hasattr(v, "deploy")
    assert hasattr(v, "build_deploy_config")


def test_build_deploy_config_requires_project(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    from nova_adk_agent.deploy.vertex import build_deploy_config

    with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_PROJECT"):
        build_deploy_config()


def test_build_deploy_config_fills_defaults(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project-123")
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_STAGING_BUCKET", raising=False)

    from nova_adk_agent.deploy.vertex import build_deploy_config

    cfg = build_deploy_config()
    assert cfg["project"] == "test-project-123"
    assert cfg["location"] == "us-central1"
    assert cfg["staging_bucket"] == "gs://test-project-123-adk-staging"
    assert cfg["display_name"] == "nova-adk-podcast-synthesizer"
    assert cfg["requirements_file"].endswith("requirements.txt")


def test_build_deploy_config_respects_overrides(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "override-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "europe-west4")
    monkeypatch.setenv("GOOGLE_CLOUD_STAGING_BUCKET", "gs://my-bucket")

    from nova_adk_agent.deploy.vertex import build_deploy_config

    cfg = build_deploy_config()
    assert cfg["location"] == "europe-west4"
    assert cfg["staging_bucket"] == "gs://my-bucket"
