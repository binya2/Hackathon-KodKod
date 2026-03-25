import mongoose from 'mongoose';

const stateSchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now },
    target_data: {
        status: String,
        location: { lat: Number, lon: Number, speed: Number },
        predicted_polygon: [[Number]]
    },
    recon_data: {
        active_drone: String,
        flight_mode: String,
        telemetry: { lat: Number, lon: Number, alt: Number }
    },
    attack_data: {
        squads: mongoose.Schema.Types.Mixed
    }
}, { collection: 'states' });

const State = mongoose.model('State', stateSchema);

export default State; 