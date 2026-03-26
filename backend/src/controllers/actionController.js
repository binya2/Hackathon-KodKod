const COMMAND_URL = 'http://localhost:8001'; // פקודות (New Target, Engage)
const STATE_URL = 'http://localhost:8000'; // מצב נוכחי 
const HISTORY_URL = 'http://localhost:8002'; // היסטוריה

// 1. יצירת מטרה חדשה והזנקה אוטומטית (חדש!)
export const handleNewTarget = async (req, res) => {
    const { lat, lon } = req.body;
    if (lat === undefined || lon === undefined) {
        return res.status(400).json({ status: 'error', message: 'Missing lat or lon' });
    }

    try {
        const response = await fetch(`${COMMAND_URL}/new_target`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: parseFloat(lat), lon: parseFloat(lon) })
        });

        const data = await response.json();
        if (!response.ok) return res.status(response.status).json(data);

        return res.status(200).json(data);
    } catch (error) {
        return res.status(500).json({ status: 'error', message: error.message });
    }
};

// 2. פקודת אש (מעודכן)
export const handleEngage = async (req, res) => {
    const { target_id, drone_id } = req.body;
    try {
        const response = await fetch(`${COMMAND_URL}/engage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: "engage",
                target_id,
                drone_id
            })
        });

        const data = await response.json();
        if (!response.ok) return res.status(response.status).json(data);

        return res.status(200).json(data);
    } catch (error) {
        return res.status(500).json({ status: 'error', message: error.message });
    }
};

// הזנקה ידנית
export const handleDeployDrone = async (req, res) => {
    const { role, target_id } = req.body;
    try {
        const response = await fetch(`${COMMAND_URL}/deploy_drone`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, target_id })
        });

        const data = await response.json();
        if (!response.ok) return res.status(response.status).json(data);

        return res.status(200).json(data);
    } catch (error) {
        return res.status(500).json({ status: 'error', message: error.message });
    }
};

// 4. החזרה לבסיס
export const handleRecall = async (req, res) => {
    const { drone_id } = req.body;
    try {
        const response = await fetch(`${COMMAND_URL}/recall_drone`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ drone_id })
        });
        const data = await response.json();
        return res.status(response.status).json(data);
    } catch (error) {
        return res.status(500).json({ status: 'error', message: error.message });
    }
};

// 5. השתלטות ידנית (Manual Move)
export const handleManualMove = async (req, res) => {
    const { drone_id, lat, lon, alt = 150.0 } = req.body;
    try {
        const response = await fetch(`${COMMAND_URL}/manual_move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                drone_id,
                lat: parseFloat(lat),
                lon: parseFloat(lon),
                alt: parseFloat(alt)
            })
        });
        const data = await response.json();
        return res.status(response.status).json(data);
    } catch (error) {
        return res.status(500).json({ status: 'error', message: error.message });
    }
};

// 6. חזרה לאוטומטי
export const handleResumeAuto = async (req, res) => {
    const { drone_id } = req.body;
    try {
        const response = await fetch(`${COMMAND_URL}/resume_auto`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ drone_id })
        });
        const data = await response.json();
        return res.status(response.status).json(data);
    } catch (error) {
        return res.status(500).json({ status: 'error', message: error.message });
    }
};

// GET STATE (Fallback)
export const getCurrentState = async (req, res) => {
    try {
        const response = await fetch(`${STATE_URL}/api/state`);
        const data = await response.json();
        res.status(200).json(data);
    } catch (error) {
        res.status(500).json({ status: 'error', message: 'Data team server offline' });
    }
};

// שליפת היסטוריית מסלול - צביעת שובל ממוקד משימה
export const getDroneHistory = async (req, res) => {
    const { droneId, targetId } = req.params;

    if (!droneId || !targetId) {
        return res.status(400).json({ status: 'error', message: 'Missing droneId or targetId' });
    }

    try {
        const response = await fetch(`${HISTORY_URL}/drone_history/${droneId}/${targetId}`);

        if (!response.ok) {
            return res.status(response.status).json({ message: "No history for this mission yet" });
        }

        const path = await response.json();
        return res.status(200).json(path);

    } catch (error) {
        console.error("History Fetch Error:", error.message);
        return res.status(500).json({ status: 'error', message: "Data Team history service offline" });
    }
};