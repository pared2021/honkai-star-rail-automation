/**
 * This is a API server
 */
import express from 'express';
import cors from 'cors';
import path from 'path';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import authRoutes from './routes/auth.js';
// for esm mode
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// load env
dotenv.config();
const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
/**
 * API Routes
 */
app.use('/api/auth', authRoutes);
/**
 * health
 */
app.use('/api/health', (req, res, next) => {
    res.status(200).json({
        success: true,
        message: 'ok'
    });
});
/**
 * error handler middleware
 */
app.use((error, req, res, next) => {
    res.status(500).json({
        success: false,
        error: 'Server internal error'
    });
});
/**
 * 404 handler
 */
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'API not found'
    });
});
export default app;
