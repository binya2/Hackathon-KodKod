import express from 'express';
import { createServer } from 'http';
import dotenv from 'dotenv';
import { Server } from 'socket.io';
import actionRout from "./routes/actionRoutes.js";

import { processMissionData } from './services/cvEngine.js';

dotenv.config();

const app = express();
app.use(express.json());

app.use("/api/actions", actionRout)

const httpServer = createServer(app);

const io = new Server(httpServer, {
    cors: {
        origin: '*',
        methods: ['GET', 'POST']
    }
});

const port = process.env.PORT || 3001;

io.on("connection", (socket) => {
    console.log(`Client connected to mission control: ${socket.id}`);

    socket.emit("conection_success", { message: "Welcome to Mission Control!" });

    socket.on('disconnect', () => {
        console.log(`Client disconnected: ${socket.id}`);
    });
});


const handleIncomingTelemetry = (rawData) => {
    try {
        const tacticalSnapshot = processMissionData(rawData);

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