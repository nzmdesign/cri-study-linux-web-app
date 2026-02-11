#!/bin/bash
exec uvicorn cri_study.main:app --host 0.0.0.0 --port 8000
