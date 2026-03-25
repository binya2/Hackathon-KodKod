import State from '../models/stateModel.js';

export const handleEngage = async (req, res) => {
    const { action, target_id, drone_id } = req.body;

    if (!action) return res.status(400).json({ status: 'error', message: 'Missing field: action' });
    if (!target_id) return res.status(400).json({ status: 'error', message: 'Missing field: target_id' });
    if (!drone_id) return res.status(400).json({ status: 'error', message: 'Missing field: drone_id' });

    try {
        console.log(`🚀 [ENGAGE COMMAND] Received at ${new Date().toISOString()}`);
        console.log(`Target: ${target_id} | Drone: ${drone_id}`);

        const response = await fetch('http://localhost:8001/engage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, target_id, drone_id })
        });

        if (!response.ok) throw new Error('Data Team API returned an error');

        const data = await response.json();

        return res.status(200).json({
            status: 'success',
            message: `Engage command for ${drone_id} received and relayed to tactical engine`,
            data: data,
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

        const response = await fetch('http://localhost:8001/engage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, drone_id, lat, lon })
        });

        if (!response.ok) throw new Error('Data Team API returned an error');

        const data = await response.json();

        return res.status(200).json({
            status: 'success',
            message: 'Navigation update successful',
            data: data,
            coordinates: { lat, lon }
        });
    } catch (error) {
        console.error('Navigation Relay Error:', error.message);
        return res.status(500).json({ status: 'error', message: 'Internal server error during navigation' });
    }
};


export const getDroneHistory = async (req, res) => {
    try {
        const { droneId } = req.params;
        const history = await State.find({ "recon_data.active_drone": droneId })
            .sort({ timestamp: -1 })
            .limit(40);

        const path = history.map(item => ({
            lat: item.recon_data.telemetry.lat,
            lng: item.recon_data.telemetry.lon
        }));

        res.status(200).json(path.reverse());
    } catch (error) {
        res.status(500).json({ status: 'error', message: error.message });
    }
};


export const getCurrentState = async (req, res) => {
    try {
        const response = await fetch('http://localhost:8000/state', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Data Team API returned an error ${error.message}`);
        }

        const data = await response.json();

        res.status(200).json(data);

    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};


export const handleDeployDrone = async (req, res) => {
    const { role } = req.body;

    if (!role || (role !== 'recon' && role !== 'attack')) {
        return res.status(400).json({
            status: 'error',
            message: 'Invalid or missing role. Must be "recon" or "attack".'
        });
    }

    try {
        console.log(`🚀 [DEPLOY COMMAND] Requesting ${role} drone deployment...`);

        const response = await fetch('http://localhost:8001/deploy_drone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role })
        });

        if (!response.ok) throw new Error('Data Team API failed to process deployment');

        const data = await response.json();

        return res.status(200).json({
            status: "deployment_request_sent",
            payload: {
                action: "DEPLOY_DRONE",
                role: role,
                timestamp: new Date().toISOString()
            },
            data_team_response: data
        });

    } catch (error) {
        console.error('Deployment Error:', error.message);
        return res.status(500).json({ status: 'error', message: 'Internal server error during deployment' });
    }
};