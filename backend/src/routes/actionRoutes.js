import express from 'express';
import {
    getCurrentState,
    handleEngage,
    handleNavigate,
    getDroneHistory,
    handleDeployDrone,
    handleAuto,
    handleNewTarget,
    handleRecallDrone,
    handCancelTarget
} from '../controllers/actionController.js';
import {handleStrikeOrder} from "../controllers/attackController.js";

const router = express.Router();

router.get('/state', getCurrentState);

// פקודת תקיפה
router.post('/engage', handleEngage);

// פקודת ניווט ידני
router.post('/navigate', handleNavigate);

router.post('/auto', handleAuto)

router.post('/new_target', handleNewTarget)

// פקודת ה-Strike.  logic 
router.post('/strike', handleStrikeOrder);

// שליפת היסטוריית מסלול של רחפן
router.get('/drone_history/:droneId/:targetId', getDroneHistory);

// פקודה לשינוי מצב של רחפן ממצב שינה לתפקיד ששולחים בבקשה 
router.post('/deploy_drone', handleDeployDrone);

router.post('/recall_drone', handleRecallDrone)

router.post('/cancel_target', handCancelTarget)

export default router;