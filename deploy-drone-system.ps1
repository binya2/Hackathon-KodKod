$ErrorActionPreference = "Continue"
$DOCKER_USER = "beni2"
$TAG = "v10"

Write-Host "--- Step 1: Nuclear Clean ---" -ForegroundColor Cyan
oc delete all,pvc,statefulset,route,configmap,secret, imagestream --all 2>$null

Write-Host "--- Step 2: Deploying Infrastructure ---" -ForegroundColor Cyan
oc apply -f k8s/openshift-deploy.yaml

Write-Host "--- Step 3: Waiting for Infrastructure (Kafka/Redis) ---" -ForegroundColor Yellow
oc wait --for=condition=Ready pod -l app=kafka --timeout=60s
oc wait --for=condition=Ready pod -l app=redis --timeout=60s

Write-Host "--- Step 4: Creating Kafka Topics ---" -ForegroundColor Cyan
$topics = @("telemetry.raw", "target.raw", "commands.drones", "commands.attack", "aggregated-state-topic", "system.logs")
foreach ($t in $topics) {
    oc exec deployment/kafka -- kafka-topics --create --topic $t --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 2>$null
}

Write-Host "--- Step 5: Building Frontend with Dynamic API ---" -ForegroundColor Cyan
$API_HOST = oc get route node-api-route -o jsonpath='{.spec.host}'
$API_URL = "https://$API_HOST"
Write-Host "Injecting API URL: $API_URL"
docker build --build-arg VITE_API_URL=$API_URL -t $DOCKER_USER/react_client:$TAG ./client
docker push $DOCKER_USER/react_client:$TAG

Write-Host "--- Step 6: Syncing Images & Restating ---" -ForegroundColor Cyan
oc set image deployment/react-client main=$DOCKER_USER/react_client:$TAG
oc rollout restart deployment/react-client
oc rollout restart deployment/state-aggregator deployment/node-backend deployment/attack-commander deployment/drone-sim deployment/target-sim

Write-Host "--- DONE ---" -ForegroundColor Green
$UI_HOST = oc get route ui-route -o jsonpath='{.spec.host}'
Write-Host "--------------------------------------------------"
Write-Host "ACCESS YOUR MAP AT: https://$UI_HOST" -ForegroundColor White
Write-Host "--------------------------------------------------"