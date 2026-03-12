# CAREER_COPILOT Stage 0 프로젝트 구조 생성 스크립트
# VS Code 터미널(PowerShell)에서 프로젝트 루트 경로에서 실행

# 디렉토리 생성
New-Item -ItemType Directory -Force -Path "infra\elasticsearch\mappings"
New-Item -ItemType Directory -Force -Path "infra\minio"
New-Item -ItemType Directory -Force -Path "infra\sqlite"
New-Item -ItemType Directory -Force -Path "backend\storage"
New-Item -ItemType Directory -Force -Path "data"
New-Item -ItemType Directory -Force -Path "models"

# __init__.py 빈 파일 생성
New-Item -ItemType File -Force -Path "backend\__init__.py"
New-Item -ItemType File -Force -Path "backend\storage\__init__.py"

Write-Host ""
Write-Host "✅ Project structure created!" -ForegroundColor Green
Write-Host ""
Write-Host "Now put the downloaded files to the paths down below:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  docker-compose.yml       → (Root)"
Write-Host "  .env.example             → (Root)"
Write-Host "  STAGE0_SETUP.md          → (Root)"
Write-Host "  verify_stage0.py         → (Root)"
Write-Host "  works_index.json         → infra\elasticsearch\mappings\"
Write-Host "  init_index.py            → infra\elasticsearch\"
Write-Host "  init_buckets.py          → infra\minio\"
Write-Host "  schema.sql               → infra\sqlite\"
Write-Host "  config.py                → backend\"
Write-Host "  main.py                  → backend\"
Write-Host "  es_client.py             → backend\storage\"
Write-Host "  minio_client.py          → backend\storage\"
Write-Host "  sqlite_client.py         → backend\storage\"