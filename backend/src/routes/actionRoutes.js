import express from 'express';
import {
    getCurrentState,
    handleEngage,
    handleManualMove,
    handleDeployDrone,
    handleResumeAuto,
    handleNewTarget,
    handleRecall,
    getDroneHistory
} from '../controllers/actionController.js';

const router = express.Router();

// 1. קבלת מצב נוכחי (Fallback ל-WebSocket)
router.get('/state', getCurrentState);

// 2. יצירת מטרה חדשה והזנקה אוטומטית (מהקליק על המפה)
router.post('/new-target', handleNewTarget);

// 3. אישור פקודת אש 
router.post('/engage', handleEngage);

// 4. הזנקה ידנית של רחפן ספציפי (Attack/Recon)
router.post('/deploy', handleDeployDrone);

// 5. פקודת חזרה לבסיס (Recall)
router.post('/recall', handleRecall);

// 6. השתלטות ידנית על מיקום הרחפן 
router.post('/manual-move', handleManualMove);

// 7. שחרור שליטה וחזרה לניהול אוטונומי
router.post('/resume-auto', handleResumeAuto);

// 8. היסטוריית מסלול ממוקדת מטרה (לצביעת השובל)
router.get('/history/:droneId/:targetId', getDroneHistory);

export default router;