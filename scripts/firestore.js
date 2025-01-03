// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { signInWithCustomToken } from "firebase/auth";
import { getFirestore, collection, getDocs, getDoc, onSnapshot, doc, addDoc, Timestamp } from "firebase/firestore";
import { getAuth } from "firebase/auth";
import { getFunctions, httpsCallable } from "firebase/functions";
import net from "net";
import "dotenv/config";

const firebaseConfig = {
  apiKey: process.env.FIRESTORE_API_KEY,
  authDomain: "dumoulin-thermal-monitoring.firebaseapp.com",
  projectId: "dumoulin-thermal-monitoring",
  storageBucket: "dumoulin-thermal-monitoring.firebasestorage.app",
  messagingSenderId: "22443848677",
  appId: "1:22443848677:web:2975681d0023bc88fe750c",
  measurementId: "G-M6SE5E5EQJ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

const db = getFirestore(app);
const auth = getAuth(app);
const functions = getFunctions(app);

let isConnected = await login();


while(!isConnected ){
    console.log("Error connecting to Firebase. Retrying in 1 second");
    isConnected = await login();
    await new Promise(resolve => setTimeout(resolve, 1000));
}

console.log("Connected to Firebase");
const camera = connectToCamera();

listenToZones(camera);
listenToSettings(camera);


function listenToZones(camera){
    onSnapshot(collection(db, "/zones"), (snapshot) => {
        const zones = {};
        snapshot.docs.forEach((doc) => {
            const data = doc.data();
            zones[doc.id] = data;
        });
        writeToCamera(camera, {
            "type": "zones",
            "data": zones
        });
    });
}

function listenToSettings(camera){
    onSnapshot(collection(db, "/settings"), (snapshot) => {
        const settings = {};
        snapshot.docs.forEach((doc) => {
            const data = doc.data();
            settings[doc.id] = data;
        });
        writeToCamera(camera, {
            "type": "settings",
            "data": settings
        });
    });
}

function sendTemperature(temperatures){
    try{
        const data = {};
        data["timestamp"] = Timestamp.now();
        data["expiration"] = Timestamp.fromDate(new Date(Date.now() + 1000*60*60*24*150)); // 150 days
        data["temperatures"] = temperatures.data;
        addDoc(collection(db, "/temperatures"), data);
    }
    catch(e){
        console.log("Error sending temperatures to Firestore");
    }
    
}

async function sendAlert(temperature) {
    try{
        const response = await httpsCallable(functions, "sendAlert",)({temperature});
        console.log("alert sent");
    }
    catch(e){
        console.log("Error sending alert");
    }
}

async function sendLog(log) {
    try{
        const data = {};
        data["timestamp"] = Timestamp.now();
        data["log"] = log;
        addDoc(collection(db, "/logs"), data);
    }
    catch(e){
        console.error(e);
        console.log("Error sending logs to Firestore");
    }
}


function writeToCamera(camera, data){
    camera.write(JSON.stringify(data)+"\n", "utf8");
}

async function login() {
    try{
        const result = await fetch(process.env.CREATE_CUSTOM_TOKEN_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"rasp_id": "raspberry-pi-1", "secret": process.env.SECRET})
        })
    
        const data = await result.json();
    
        if(data.token === undefined){
            return false;
        }
    
        const token = data.token;
        await signInWithCustomToken(auth, token);
        return true;
    }
    catch(e){
        return false;
    }
}

function connectToCamera() {
    const camera = new net.Socket();
    camera.connect(process.env.PORT, process.env.HOST, () => {
        console.log("Connected to Python script");
    });

    camera.on('data', (data) => {
        try{
            data = data.toString("utf8");
            print("data utf8 : " + data);
            const parsedData = JSON.parse(data);

            if(parsedData.type == "temperatures"){
                sendTemperature(parsedData);
            }
            else if(parsedData.type == "alert"){
                sendAlert(parsedData.data.temperature);
            }
            else if(parsedData.type == "log"){
                print("logging : " + parsedData.data);
                sendLog(parsedData.data);
            }
            else{
                throw new Error("Unknown data type");
            }
        }catch(e){
            console.log("Error parsing data from camera");
        } 
    });

    camera.on('close', () => {
        console.log("Connection closed");
    });

    return camera;
}