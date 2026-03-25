import express from 'express';
import { createServer } from 'http';
import dotenv from 'dotenv';
import { Server } from 'socket.io';
import actionRout from "./routes/actionRoutes.js";

import { processMissionData } from './services/cvEngine.js';
import { calculateHitDamage } from './controllers/attackController.js';

dotenv.config();

const app = express();
app.use(express.json());

app.use("/api/actions", actionRout)

const httpServer = createServer(app);
let currentTargetStatus = 'moving';

const io = new Server(httpServer, {
    cors: {
        origin: '*',
        methods: ['GET', 'POST']
    }
});

const port = process.env.PORT || 3001;

io.on("connection", (socket) => {
    console.log(`Client connected to mission control: ${socket.id}`);

    socket.on('PAYLOAD_DROPPED', (data) => {
        const newStatus = calculateHitDamage(data.payload_loc, data.target_loc);
        currentTargetStatus = newStatus;

        console.log(`[BATTLE LOG] Target status updated to: ${newStatus}`);

        io.emit('TARGET_HIT_CONFIRMED', { status: newStatus, location: data.payload_loc });
    });

    socket.emit("conection_success", { message: "Welcome to Mission Control!" });

    socket.on('disconnect', () => {
        console.log(`Client disconnected: ${socket.id}`);
    });
});


const handleIncomingTelemetry = (rawData) => {
    try {
        const tacticalSnapshot = processMissionData(rawData);

        if (tacticalSnapshot) {
            if (!tacticalSnapshot.target_data) {
                tacticalSnapshot.target_data = {};
            }
            tacticalSnapshot.target_data.status = currentTargetStatus;
        }

        io.emit('tactical_update', tacticalSnapshot);

        console.log(`Processed telemetry at ${tacticalSnapshot.timestamp}`);
    } catch (error) {
        console.error('Error processing mission data:', error.message);
    }
}

httpServer.listen(port, () => {
    console.log(`Mission control server is live on port: ${port}`);
});

import { getMockData } from './mock/initialData.js';

setInterval(() => {
    handleIncomingTelemetry(getMockData());
}, 500);

setInterval(() => {
    const freshData = getMockData();
    handleIncomingTelemetry(freshData);
}, 500);