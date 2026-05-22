import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyBCquNrbQnQVjNhdsA6yDx0paGZKAXpsIM",
  authDomain: "project1-8ec21.firebaseapp.com",
  projectId: "project1-8ec21",
  storageBucket: "project1-8ec21.firebasestorage.app",
  messagingSenderId: "1019842469994",
  appId: "1:1019842469994:web:e3df12708cd4a96e46ea13",
  measurementId: "G-L6F3M30KTS"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { auth };
