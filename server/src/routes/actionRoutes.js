import express from 'express';
import { handleEngage, handleNavigate } from '../controllers/actionController.js';

const router = express.Router();

router.post('/engage', handleEngage);
router.post('/navigate', handleNavigate);

export default router;