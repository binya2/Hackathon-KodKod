import express from 'express';
import { getCurrentState, handleEngage, handleNavigate, getDroneHistory } from '../controllers/actionController.js';
import {handleStrikeOrder} from "../controllers/attackController.js";

const router = express.Router();

router.get('/state', getCurrentState);

// פקודת תקיפה
router.post('/engage', handleEngage);

// פקודת ניווט ידני
router.post('/navigate', handleNavigate);

// פקודת ה-Strike.  logic 
router.post('/strike', handleStrikeOrder);

// שליפת היסטוריית מסלול של רחפן
router.get('/history/:droneId', getDroneHistory);

export default router;