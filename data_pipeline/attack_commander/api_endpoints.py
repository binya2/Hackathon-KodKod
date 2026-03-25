from fastapi import APIRouter, HTTPException
from data_pipeline.attack_commander.models import (
    EngageRequest,
    DeployRequest,
    NewTargetRequest,
    RecallRequest,
    ManualMoveRequest,
    ResumeAutoRequest,
)
from data_pipeline.attack_commander.services import (
    execute_engage,
    execute_drone_deployment,
    spawn_target_with_swarm,
    execute_recall,
    execute_manual_move,
    execute_resume_auto
)

router = APIRouter()


@router.post("/engage")
async def engage(req: EngageRequest):
    if req.action != "engage":
        raise HTTPException(status_code=400, detail="Invalid action.")
    
    try:
        payload = await execute_engage(req.drone_id, req.target_id)
        return {"status": "command_sent", "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy_drone")
async def deploy_drone(req: DeployRequest):
    if req.role not in ["recon", "attack"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'recon' or 'attack'.")
    
    try:
        payload = await execute_drone_deployment(req.role, req.target_id)
        return {"status": "deployment_request_sent", "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new_target")
async def new_target(req: NewTargetRequest):
    try:
        target_id, intel_payload = await spawn_target_with_swarm(req.lat, req.lon)
        return {
            "status": "target_spawned_and_swarm_deployed",
            "target_id": target_id,
            "intel_payload": intel_payload,
            "deployment_count": 3
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recall_drone")
async def recall_drone(req: RecallRequest):
    try:
        payload = await execute_recall(req.drone_id)
        return {"status": "recall_sent", "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual_move")
async def manual_move(req: ManualMoveRequest):
    try:
        payload = await execute_manual_move(req.drone_id, req.lat, req.lon, req.alt)
        return {"status": "manual_move_sent", "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume_auto")
async def resume_auto(req: ResumeAutoRequest):
    try:
        payload = await execute_resume_auto(req.drone_id)
        return {"status": "resume_auto_sent", "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "up"}
