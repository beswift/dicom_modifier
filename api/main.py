from fastapi.responses import StreamingResponse
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import verify_password, create_access_token, get_password_hash
from models import User, UserInDB
from datetime import timedelta
from pydicom import dcmread
from pydicom.filebase import DicomBytesIO
from fastapi import Depends, FastAPI, HTTPException, status
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import User, UserInDB
from auth import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash, verify_password, create_access_token
import json
import random
import string
import shutil
import os
import logging
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware



# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the logger instance
logger = logging.getLogger(__name__)



# Use the logger in your endpoints



app = FastAPI()

# Enable CORS for all origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy database record
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": get_password_hash("secret"),
        "disabled": False,
    }
}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = username
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data)
    if user is None:
        raise credentials_exception
    return user

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# A simple endpoint to test authentication
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

TEMP_DIR = "temp_files"
# Make sure the temporary directory exists
os.makedirs(TEMP_DIR, exist_ok=True)
@app.post("/upload-dicom/")
async def upload_dicom(file: UploadFile = File(...)):
    try:
        # Read the file using pydicom
        dicom_bytes = await file.read()
        dicom_dataset = dcmread(DicomBytesIO(dicom_bytes))

        # Perform operations on the DICOM dataset here
        # ...

        return {"filename": file.filename, "tags": str(dicom_dataset)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/extract-tags/")
async def extract_tags(file: UploadFile = File(...)):
    try:
        dicom_bytes = await file.read()
        dataset = dcmread(DicomBytesIO(dicom_bytes))

        # Initialize a dictionary to hold the tags and values
        tags_dict = {}

        # Iterate through the dataset and add each value to the dictionary
        for tag in dataset.dir():
            data_element = dataset.get(tag)
            if data_element:  # Ensure the data element exists
                # Convert the tag to a string and get a human-readable value
                tags_dict[str(data_element.tag)] = str(data_element.value)

        # Now you have a dictionary with the tags and values, convert it to JSON
        return json.dumps(tags_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/modify-tags/")
async def modify_tags(file: UploadFile = File(...), tags: str = Form(...), current_user: User = Depends(get_current_user)):
    try:
        dicom_bytes = await file.read()
        logger.info(f"Received file: {file.filename}")
        dataset = dcmread(DicomBytesIO(dicom_bytes))

        # Convert the JSON string back to a dictionary
        tags_to_modify = json.loads(tags)

        # Modify the tags in the dataset
        for tag, value in tags_to_modify.items():
            setattr(dataset, tag, value)

        # Save the modified dataset to a buffer
        buffer = DicomBytesIO()
        dataset.save_as(buffer, write_like_original=True)
        buffer.seek(0)


        # Return the modified DICOM file
        return StreamingResponse(buffer, media_type="application/dicom")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}
@app.get("/generate-random-name/")
async def generate_random_name():
    # Generate a random name using a simple method for demonstration
    name = ''.join(random.choices(string.ascii_uppercase, k=5))
    logger.info(f"Generated random name: {name}")
    return {"random_name": f"Patient^{name}"}

@app.post("/save-and-download/")
async def save_and_download(file: UploadFile = File(...), tags: str = Form(...)):
    try:
        dicom_bytes = await file.read()
        logger.info(f"Received file: {file.filename}")
        dataset = dcmread(DicomBytesIO(dicom_bytes))
        logger.info(f"Received tags: {tags}")
        tags_to_modify = json.loads(tags)
        logger.info(f"Tags to modify: {tags_to_modify}")
        for tag, value in tags_to_modify.items():
            setattr(dataset, tag, value)

        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(TEMP_DIR, filename)
        logger.info(f"Saving file to {file_path}")

        # Save the modified dataset to a file
        dataset.save_as(file_path)

        # Return a response to download the file
        return FileResponse(path=file_path, filename=filename, media_type='application/dicom')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Scheduled job for cleanup
@app.on_event("startup")
async def startup_event():
    # This could be expanded with a more robust job scheduler
    # For example, you could use 'apscheduler' to run cleanup jobs periodically
    logger.info("Starting scheduled job for cleanup")
    cleanup_old_files()

def cleanup_old_files():
    # Get the current time
    now = datetime.now()
    # List all files in the temporary directory
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        # Get the modification time and convert it to a datetime object
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        # If the file is older than 1 day, delete it
        if (now - file_mod_time).days > 1:
            os.remove(file_path)
