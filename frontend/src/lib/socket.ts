import { io, Socket } from 'socket.io-client';
import { API_URL   } from '@/config';
const SOCKET_URL = API_URL.replace(/^http/, 'ws');

let socket: Socket | null = null;

export const initSocket = () => {
  if (!socket) {
    socket = io(SOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
    });
  }
  return socket;
};

export const getSocket = () => {
  if (!socket) {
    return initSocket();
  }
  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};
