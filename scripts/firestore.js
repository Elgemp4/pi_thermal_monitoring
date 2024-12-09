// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { signInWithCustomToken } from "firebase/auth";
import { getFirestore, collection, getDocs, getDoc, onSnapshot, doc, addDoc, Timestamp } from "firebase/firestore";
import { getAuth } from "firebase/auth";
import net from "net";
import "dotenv/config";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCCHE7OpbwEze_VZrn-XRtoZhnjA6RhoLU",
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

const isConnected = await login();

if(isConnected){
    console.log("Connected to Firebase");
    const camera = connectToCamera();

    listenToZones(camera);
    listenToSettings(camera);
}

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
    const data = {}
    data["timestamp"] = Timestamp.now();
    data["expiration"] = Timestamp.fromDate(new Date(Date.now() + 1000*60*60*24*150)); // 150 days
    data["temperatures"] = temperatures.data;
    addDoc(collection(db, "/temperatures"), data);
}


function writeToCamera(camera, data){
    camera.write(JSON.stringify(data)+"\n", "utf8");
}

async function login() {

    const result = await fetch("https://createcustomtoken-l4fnrox4cq-uc.a.run.app", {
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

function connectToCamera(){
    const camera = new net.Socket();
    camera.connect(process.env.PORT, process.env.HOST, () => {
        console.log("Connected to Python script");
    });

    camera.on('data', (data) => {
        try{
            data = data.toString("utf8");

            const parsedData = JSON.parse(data);

            if(parsedData.type == "temperatures"){
                sendTemperature(parsedData);
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

