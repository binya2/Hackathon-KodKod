export const handleEngage = async (req, res) => {
    const { action, target_id, drone_id } = req.body;

    if (!action) return res.status(400).json({ status: 'error', message: 'Missing field: action' });
    if (!target_id) return res.status(400).json({ status: 'error', message: 'Missing field: target_id' });
    if (!drone_id) return res.status(400).json({ status: 'error', message: 'Missing field: drone_id' });

    try {
        console.log(`🚀 [ENGAGE COMMAND] Received at ${new Date().toISOString()}`);
        console.log(`Target: ${target_id} | Drone: ${drone_id}`);

        /*
         * const response = await fetch('כאן תכניסו את הכתובת לדאטא שלכם שהשרת יעשה לזה קריאה ונוכל לעבוד עם הדאטא עצמו. http://data-aggregator-api/command סגנון הקוד שתצטרכו להשלים: ', {
         * method: 'POST',
         * headers: { 'Content-Type': 'application/json' },
         * body: JSON.stringify({ action, target_id, drone_id })
         * });
         */

        return res.status(200).json({
            status: 'success',
            message: `Engage command for ${drone_id} received and relayed to tactical engine`,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error:', error.message);
        return res.status(500).json({ status: 'error', message: 'Failed to relay command' });
    }
};

export const handleNavigate = async (req, res) => {
    const { action, drone_id, lat, lon } = req.body;

    if (!action) return res.status(400).json({ status: 'error', message: 'Missing field: action' });
    if (!drone_id) return res.status(400).json({ status: 'error', message: 'Missing field: drone_id' });
    if (lat === undefined || lat === null) return res.status(400).json({ status: 'error', message: 'Missing field: lat' });
    if (lon === undefined || lon === null) return res.status(400).json({ status: 'error', message: 'Missing field: lon' });

    try {
        console.log(`📍 [NAVIGATION COMMAND] Received at ${new Date().toISOString()}`);
        console.log(`Drone ID: ${drone_id} to Coordinates: ${lat}, ${lon}`);

        /*
         * const response = await fetch('כאן תכניסו את הכתובת לדאטא שלכם שהשרת יעשה לזה קריאה ונוכל לעבוד עם הדאטא עצמו. http://data-aggregator-api/command סגנון הקוד שתצטרכו להשלים: ', {
         * method: 'POST',
         * headers: { 'Content-Type': 'application/json' },
         * body: JSON.stringify({ action, drone_id, lat, lon })
         * });
         */

        return res.status(200).json({
            status: 'success',
            message: 'Navigation update successful',
            coordinates: { lat, lon }
        });
    } catch (error) {
        console.error('Navigation Relay Error:', error.message);
        return res.status(500).json({ status: 'error', message: 'Internal server error during navigation' });
    }
};