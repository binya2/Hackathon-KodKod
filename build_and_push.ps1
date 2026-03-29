$ErrorActionPreference = "Stop"

$DOCKER_USER = "beni2"
$TAG = "v1"

# !!! חובה לשנות את הכתובת הזו לראוט האמיתי שנוצר ב-OpenShift לפני שמריצים !!!
$API_URL = "https://node-api-route-YOUR-PROJECT.apps.openshift.com"

Write-Host "Logging in to Docker Hub..." -ForegroundColor Cyan
docker login -u $DOCKER_USER

# הגדרת כל שירותי ה-Python (הקונטקסט שלהם הוא תיקיית data_pipeline)
$DataPipelineServices = @(
    @{ Name = "state_aggregator"; Dockerfile = "state_aggregator/Dockerfile" },
    @{ Name = "attack_commander"; Dockerfile = "attack_commander/Dockerfile" },
    @{ Name = "history_service";  Dockerfile = "history_writer/Dockerfile" },
    @{ Name = "attack_brain";     Dockerfile = "attack_brain/Dockerfile" },
    @{ Name = "recon_brain";      Dockerfile = "recon_brain/Dockerfile" },
    @{ Name = "drone_sim";        Dockerfile = "edge_simulators/Dockerfile" },
    @{ Name = "target_sim";       Dockerfile = "edge_simulators/Dockerfile" },
    @{ Name = "log_aggregator";   Dockerfile = "log_aggregator/Dockerfile" }
)

Write-Host "`n--- Building Data Pipeline Services ---" -ForegroundColor Yellow
foreach ($svc in $DataPipelineServices) {
    $imageName = "$DOCKER_USER/$($svc.Name):$TAG"
    Write-Host "Building and pushing: $imageName" -ForegroundColor Green

    docker build -t $imageName -f "data_pipeline/$($svc.Dockerfile)" ./data_pipeline
    docker push $imageName
}

Write-Host "`n--- Building Fullstack Services ---" -ForegroundColor Yellow

# Backend (Node.js)
$backendImage = "$DOCKER_USER/node_backend:$TAG"
Write-Host "Building and pushing: $backendImage" -ForegroundColor Green
docker build -t $backendImage ./backend
docker push $backendImage

# Frontend (React) - שימוש ב-Build Arg
$frontendImage = "$DOCKER_USER/react_client:$TAG"
Write-Host "Building and pushing: $frontendImage" -ForegroundColor Green
docker build --build-arg VITE_API_URL=$API_URL -t $frontendImage ./client
docker push $frontendImage

Write-Host "`n✅ All images successfully built and pushed to Docker Hub!" -ForegroundColor Cyan