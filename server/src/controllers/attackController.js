import { getDistanceInMeters } from "../utils/distanceCalculator.js";

const DATA_TEAM_URL = 'http://data-api:5000/execute';

export const handleStrikeOrder = async (req, res) => {
    const { drone_id, target_id } = req.body;

    try {
        console.log(`[C2] Fire Order: Drone ${drone_id} targets ${target_id}`);

        const response = await fetch(DATA_TEAM_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'EXECUTE_STRIKE',
                drone_id,
                target_id
            }),
        });

        if (!response.ok) throw new Error('Data team API error');

        res.json({ success: true, message: 'Engage command sent successfully' });
    } catch (error) {
        console.error('Engage Error:', error.message);
        res.status(500).json({ error: 'Failed to relay fire command' });
    }
};

export const calculateHitDamage = (payloadLocation, targetLocation) => {
    const distance = getDistanceInMeters(payloadLocation, targetLocation);

    console.log(`[BDA] Impact distance: ${distance.toFixed(2)}m`);

    if (distance <= 5) {
        return 'destroyed'
    }
    if (distance <= 15) {
        return 'damaged'
    } else {
        return 'moving';
    }
};