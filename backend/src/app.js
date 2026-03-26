import express from 'express';
import { createServer } from 'http';
import dotenv from 'dotenv';
import { Server } from 'socket.io';
import actionRoutes from "./routes/actionRoutes.js";
import cors from 'cors';
import { processMissionData } from './services/cvEngine.js';

dotenv.config();

const app = express();
app.use(express.json());
app.use(cors());

app.use("/api/actions", actionRoutes);

const httpServer = createServer(app);

const io = new Server(httpServer, {
    cors: {
        origin: 'http://localhost:8000',
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

httpServer.listen(port, () => {
    console.log(`Mission control server is live on port: ${port}`);
});

// סימולציה של נתונים (Mock) - בייצור זה יוחלף בהאזנה ל-Data Team
import { getMockData } from './mock/initialData.js';

setInterval(() => {
    const freshData = "http://localhost:8002";
    handleIncomingTelemetry(freshData);
}, 500);