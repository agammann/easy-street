"""Explicit hosted entry point; never loads a local developer's .env files."""
from .judging import DemoSettings, JudgingApplication

app = JudgingApplication(DemoSettings.from_env())
