import streamlink
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
# cors
from fastapi.middleware.cors import CORSMiddleware
import subprocess
from ultralytics import YOLO
import cv2
import os
import whisper
# load pretrained model
model = YOLO('yolov8x.pt')

whisperModel = whisper.load_model("base")


# cors
origins = ["*"]

app = FastAPI()

import time
import asyncio


def getStreamUrl(user):
    streams = streamlink.streams("https://www.twitch.tv/" + user)
    # check if 720 stream is online if not use 480
    if "720p" in streams:
        url = streams["720p"].url
    elif "480p" in streams:
        url = streams["480p"].url
    else:
        url = streams["best"].url
    return url

async def transcribeAudio(url):
    print("transcribeAudio")

    while True:
        try:
            print("while")
            # Open stream for 10 seconds
            command = ['ffmpeg', '-i', url, '-t', '5', '-y', 'audio.wav']
            # Run the command wihout verbosity
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # wait for 10 seconds
            #await asyncio.sleep(5)
            result = whisperModel.transcribe("audio.wav")
            print(result["text"])
            yield result["text"]
        except KeyboardInterrupt:
            break



async def streamVideo(url, fps=24):
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame_time = 1.0 / fps

    while True:
        try:
            start_time = time.time()
            ret, frame = cap.read()

            if ret:
                # Detect objects (if you want to)
                results = model.predict(frame, conf=0.70, device=0,  verbose=False)
                
                #Display the box and label overlays
                for result in results :
                    boxes = result.boxes.xyxy
                    i = 0
                    for box in boxes:
                        cls = int(result.boxes.cls[i])
                        #print(cls)
                        className = result.names[cls]

                        xmin, ymin, xmax, ymax = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                        # Draw the bounding box
                        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
                        # Draw label and confidence
                        cv2.putText(frame, className, (xmin, ymin - 13), cv2.FONT_HERSHEY_SIMPLEX, 1e-3 * frame.shape[0], (0, 0, 255), 2)
                        i = i + 1
                    #await asyncio.sleep(3)

                # limit capture buffer size
                # Convert frame to bytes
                _, buffer = cv2.imencode('.jpg', frame)

                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                elapsed_time = time.time() - start_time

                # Adjust frame time based on actual processing time
                frame_time_adjusted = max(frame_time - elapsed_time, 0)
                #print(frame_time_adjusted)
                await asyncio.sleep(frame_time_adjusted)

        except KeyboardInterrupt:
            break

# audio
@app.get("/audio/{user}")
async def audio(user: str):
    # Open the stream and save as audio.wav
    streams = streamlink.streams("https://www.twitch.tv/" + user)
    url = streams["audio_only"].url
    #transcribeAudio(url)
    # Return text into a websocket
    return StreamingResponse(transcribeAudio(url), media_type="text/plain")
# realtime
@app.get("/realtime/{user}")
async def realtime(user: str):
    # Open the stream
    streams = streamlink.streams("https://www.twitch.tv/" + user)
    url = streams["720p"].url   
    #print(streams) 480p
    
    return StreamingResponse(streamVideo(url), media_type="multipart/x-mixed-replace;boundary=frame")

# stream/user
@app.get("/stream/{user}")
async def stream(user: str):
    # Open the stream
    streams = streamlink.streams("https://www.twitch.tv/" + user)
    url = streams["best"].url   

    folderPath = "stream/" + user 
    # if stream folder does not exist
    if not os.path.exists("stream"):
        # create folder
        os.system("mkdir stream")


    # remove folder if exists 
    if os.path.exists(user):
        # remove folder and all files
        os.system("rm -rf " + folderPath)
        # create folder
        os.system("mkdir " + folderPath)
    else:
        # create folder
        os.system("mkdir " + folderPath)

    path = folderPath + "/stream.jpg"
    # ffmpeg -i pipe:0 -filter:v fps=4 -updatefirst 1 live.jpeg
    # overwrite yes
    command = ['ffmpeg', '-i', url, '-y', path]

    # Run the command
    subprocess.run(command)

    # Detect objects
    results = model.predict(path, save=True, conf=0.40, project=folderPath, device=0)

    for result in results :
        path = result.save_dir
        print(result.save_dir)


    # Return the image
    return FileResponse(path + "/stream.jpg")
