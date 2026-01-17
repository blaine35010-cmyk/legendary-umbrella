# Stop Court AI Container
Write-Host "Stopping and removing court-ai-app container"
docker stop court-ai-app 2>$null
docker rm court-ai-app 2>$null
Write-Host "Container stopped."