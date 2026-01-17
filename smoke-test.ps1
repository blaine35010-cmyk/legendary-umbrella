# Smoke Test for Court AI
param(
    [string]$ImageTag = "v1.3.3",
    [string]$DropboxPath = "C:\Users\blain\Dropbox\Master_Court_Files",
    [string]$OpenAIKey = ""
)

Write-Host "Running smoke test for Court AI"

# Start container
Write-Host "Starting container..."
$envVars = "-e CASE_ROOT=""/app/dropbox"""
if ($OpenAIKey) {
    $envVars += " -e OPENAI_API_KEY=""$OpenAIKey"""
}
docker run -d --name court-ai-smoke -p 8002:8000 -v "${DropboxPath}:/app/dropbox" $envVars "ghcr.io/blaine35010-cmyk/court-ai:$ImageTag"

Start-Sleep -Seconds 10  # Wait for startup

# Test health
Write-Host "Testing health endpoint..."
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8002/health" -Method GET
    if ($health.StatusCode -eq 200) {
        Write-Host "Health check passed"
    } else {
        throw "Health check failed"
    }
} catch {
    Write-Host "Health check failed: $_"
    docker stop court-ai-smoke
    docker rm court-ai-smoke
    exit 1
}

# Test ask
Write-Host "Testing ask endpoint..."
try {
    $body = @{question = "What is the divorce decree?"; format = "compact"} | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "http://localhost:8002/ask" -Method POST -Body $body -ContentType "application/json"
    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        if ($result.answer) {
            Write-Host "Ask test passed"
        } else {
            throw "No answer in response"
        }
    } else {
        throw "Ask request failed"
    }
} catch {
    Write-Host "Ask test failed: $_"
    docker stop court-ai-smoke
    docker rm court-ai-smoke
    exit 1
}

# Stop container
Write-Host "Stopping test container..."
docker stop court-ai-smoke
docker rm court-ai-smoke

Write-Host "Smoke test passed!"