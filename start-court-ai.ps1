# Start Court AI Container
param(
    [string]$ImageTag = "v1.3.0",
    [string]$DropboxPath = "C:\Users\blain\Dropbox\Master_Court_Files"
)

Write-Host "Pulling image ghcr.io/blaine35010-cmyk/court-ai:$ImageTag"
docker pull "ghcr.io/blaine35010-cmyk/court-ai:$ImageTag"

Write-Host "Stopping existing container if running"
docker stop court-ai-app 2>$null
docker rm court-ai-app 2>$null

Write-Host "Starting container with volume mount"
docker run -d --name court-ai-app -p 8001:8000 -v "${DropboxPath}:/app/dropbox" -e CASE_ROOT="/app/dropbox" "ghcr.io/blaine35010-cmyk/court-ai:$ImageTag"

Write-Host "Container started. Access UI at http://localhost:8001"