import express from 'express';
import { createServer } from 'http';
import dotenv from 'dotenv';
import { Server } from 'socket.io';
import actionRoutes from "./routes/actionRoutes.js";
import cors from 'cors';
import { processMissionData } from './services/cvEngine.js';
import WebSocket from 'ws';

dotenv.config();

const app = express();
app.use(express.json());
app.use(cors());

app.use("/api/actions", actionRoutes);

const httpServer = createServer(app);

const io = new Server(httpServer, {
    cors: {
        origin: 'http://localhost:5173',
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

        if (tacticalSnapshot) {
            io.emit('tactical_update', tacticalSnapshot);
        }

    } catch (error) {
        console.error('Error processing mission data:', error.message);
    }
}



const dataStream = new WebSocket('ws://localhost:8000/ws');

dataStream.on('open', () => {
    console.log("Successfully connected to Data Team's live stream (Port 8000)");
});

dataStream.on('message', (message) => {
    try {
        const freshData = JSON.parse(message);

        handleIncomingTelemetry(freshData);
    } catch (error) {
        console.error('Data parsing error:', error.message);
    }
});

dataStream.on('error', (err) => {
    console.error('Data connection error:', err.message);
});


httpServer.listen(port, () => {
    console.log(`Mission control server is live on port: ${port}`);
});