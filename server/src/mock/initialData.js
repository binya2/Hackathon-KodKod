let baseLat = 31.7;
let baseLon = 35.2;

export const getMockData = () => {
    baseLat += 0.0001;
    baseLon += 0.0001;

    return {
        timestamp: new Date().toISOString(),
        target_data: {
            status: "moving",
            location: {
                lat: baseLat,
                lon: baseLon,
                speed: 60
            },
            predicted_polygon: []
        },
        recon_data: {
            active_drone: "DRN-RECON-1",
            flight_mode: "AUTO",
            telemetry: {
                lat: baseLat + 0.002,
                lon: baseLon + 0.002,
                alt: 200
            },
            video_stream_url: "ws://..."
        },
        attack_data: {
            squads: [
                {
                    squad_id: "SQUAD-ALPHA",
                    drones: [
                        {
                            drone_id: "DRN-ATK-1",
                            telemetry: {
                                lat: baseLat - 0.005,
                                lon: baseLon - 0.005,
                                alt: 100
                            },
                            weapons_ready: 2,
                            status: "awaiting_command"
                        }
                    ]
                }
            ]
        }
    };
};