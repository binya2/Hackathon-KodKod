import { getDistanceInMeters } from "../utils/distanceCalculator.js";


const VISIBILITY_RADIUS_METERS = 100;


export const processMissionData = (rawData) => {

    const droneLoc = rawData.recon_data.telemetry;
    const targetLoc = rawData.target_data.location;

    const distance = getDistanceInMeters(
        { lat: droneLoc.lat, lon: droneLoc.lon },
        { lat: targetLoc.lat, lon: targetLoc.lon }
    );

    const isVisible = distance <= VISIBILITY_RADIUS_METERS;

    return {
        timestamp: rawData.timestamp,
        recon: rawData.recon_data,
        attack_squads: rawData.attack_data.squads,

        target: isVisible ? rawData.target_data : null,

        metadata: {
            distanceToTarget: Math.round(distance),
            isTargetLocked: isVisible
        }
    };
};