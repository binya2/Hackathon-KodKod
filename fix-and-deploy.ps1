$ErrorActionPreference = "Stop"

Write-Host "--- Step 1: Cleaning OpenShift Environment ---" -ForegroundColor Cyan
oc delete all,pvc,route --all

Write-Host "--- Step 2: Applying Updated Infrastructure ---" -ForegroundColor Cyan
oc apply -f k8s/openshift-deploy.yaml

Write-Host "--- Step 3: Waiting for Kafka to stabilize (30s) ---" -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "--- Step 4: Creating Kafka Topics Manually ---" -ForegroundColor Cyan
$topics = @("telemetry.raw", "target.raw", "commands.drones", "commands.attack", "aggregated-state-topic", "system.logs")
foreach ($topic in $topics) {
    Write-Host "Creating topic: $topic"
    # Redirecting error to null in case topic already exists
    oc exec deployment/kafka -- kafka-topics --create --topic $topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 2>$null
}

Write-Host "--- Step 5: Restarting Python Services ---" -ForegroundColor Cyan
oc rollout restart deployment/state-aggregator deployment/drone-sim deployment/target-sim deployment/attack-brain deployment/recon-brain

Write-Host "--- Step 6: Building and Pushing React v10 ---" -ForegroundColor Cyan
$API_URL = "https://node-api-route-beny20-dev.apps.rm2.thpm.p1.openshiftapps.com"
docker build --build-arg VITE_API_URL=$API_URL -t beni2/react_client:v10 ./client
docker push beni2/react_client:v10

Write-Host "--- Step 7: Finalizing OpenShift Image ---" -ForegroundColor Cyan
oc set image deployment/react-client main=beni2/react_client:v10
oc rollout restart deployment/react-client

Write-Host "`n Deployment Finished! Wait 60 seconds for everything to sync." -ForegroundColor Green
$UI_HOST = oc get route ui-route -o jsonpath='{.spec.host}'
Write-Host "ACCESS YOUR MAP AT: https://$UI_HOST" -ForegroundColor White