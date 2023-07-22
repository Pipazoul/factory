import streamlink
from fastapi import FastAPI
from fastapi.responses import FileResponse
# cors
from fastapi.middleware.cors import CORSMiddleware
import subprocess
from ultralytics import YOLO
import cv2
import os

# load pretrained model
model = YOLO('yolov8x.pt')

# cors
origins = ["*"]

app = FastAPI()

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
