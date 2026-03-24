import express from 'express';
import { handleEngage, handleNavigate } from '../controllers/actionController.js';
import {handleStrikeOrder} from "../controllers/attackController.js";

const router = express.Router();

router.post('/engage', handleEngage);
router.post('/navigate', handleNavigate);
router.post('/strike', handleStrikeOrder);

export default router;